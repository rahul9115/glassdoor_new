"""
main.py

Given a company's landing page on Glassdoor and an output filename, scrape the
following information about each employee review:

Review date
Employee position
Employee location
Employee status (current/former)
Review title
Number of helpful votes
Pros text
Cons text
Advice to mgmttext
Ratings for each of 5 categories
Overall rating
"""

import time
import pandas as pd
from argparse import ArgumentParser

import logging.config
from selenium import webdriver as wd
from selenium.webdriver import ActionChains
import selenium
import numpy as np
from selenium.webdriver.common.by import By

from schema import SCHEMA
import json
import urllib
import urllib.parse
import datetime as dt
import os

start = time.time()

check_for_config = os.path.exists("config.xlsx")

if not check_for_config:
    print("Config file does not exists")
    exit()

DEFAULT_URL = 'https://www.glassdoor.co.in/Reviews/LTI-Reviews-E30653.htm'

parser = ArgumentParser()
'''

parser.add_argument('-u', '--url',
                   help='URL of the company\'s Glassdoor landing page.',
                   default=DEFAULT_URL)
parser.add_argument('-f', '--file', default='glassdoor_ratings.csv',
                    help='Output file.')
parser.add_argument('--headless', action='store_true',
                    help='Run Chrome in headless mode.')
'''
parser.add_argument('--username', help='Email address used to sign in to GD.')
parser.add_argument('-p', '--password', help='Password to sign in to GD.')
parser.add_argument('-c', '--credentials', help='Credentials file')

# parser.add_argument('-l', '--limit', default=25,
#                     action='store', type=int, help='Max reviews to scrape')

# parser.add_argument('--start_from_url', action='store_true',
#                     help='Start scraping from the passed URL.')
parser.add_argument(
    '--max_date', help='Latest review date to scrape.\
    Only use this option with --start_from_url.\
    You also must have sorted Glassdoor reviews ASCENDING by date.',
    type=lambda s: dt.datetime.strptime(s, "%Y-%m-%d"))

parser.add_argument(
    '--min_date', help='Earliest review date to scrape.\
    Only use this option with --start_from_url.\
    You also must have sorted Glassdoor reviews DESCENDING by date.',
    type=lambda s: dt.datetime.strptime(s, "%Y-%m-%d"))

args = parser.parse_args()

# if not args.start_from_url and (args.max_date or args.min_date):
#     raise Exception(
#         'Invalid argument combination:\
#         No starting url passed, but max/min date specified.'
#     )


try:
    with open('secret.json') as f:
        d = json.loads(f.read())
        args.username = d['username']
        args.password = d['password']
except FileNotFoundError:
    msg = 'Please provide Glassdoor credentials.\
    Credentials can be provided as a secret.json file in the working\
    directory, or passed at the command line using the --username and\
    --password flags.'
    raise Exception(msg)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(lineno)d\
    :%(filename)s(%(process)d) - %(message)s')
ch.setFormatter(formatter)

logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('selenium').setLevel(logging.CRITICAL)


def scrape(field, review, author):
    def scrape_date(review):
        jobtitle = author.find_element(By.CLASS_NAME, 'authorJobTitle').text.strip('"')
        print(jobtitle)
        print(jobtitle.split('-')[0].strip(' '), '%d, %b, %Y')
        res = dt.datetime.strptime(jobtitle.split('-')[0].strip(' ').upper().replace("SEPT", "Sep"), '%d %b %Y').date()
        return res

    def scrape_emp_title(review):
        if 'Anonymous Employee' not in review.text:
            try:
                jobtitle = review.find_element(By.CLASS_NAME, 'authorJobTitle').text.strip('"')
                res = jobtitle.split('-')[1].strip(' ')
            except Exception:
                logger.warning('Failed to scrape employee_title')
                res = "N/A"
        else:
            res = "Anonymous"
        return res

    def scrape_location(review):
        if 'in' in review.text:
            try:
                res = author.find_element(By.CLASS_NAME, 'authorLocation').text
            except Exception:
                logger.warning('Failed to scrape employee_location')
                res = np.nan
        else:
            res = "N/A"
        return res

    def scrape_status(review):
        try:
            res = review.find_element(By.CLASS_NAME, 'pt-xsm').text.strip('"')
        except Exception:
            logger.warning('Failed to scrape employee_status')
            res = "N/A"
        return res

    def scrape_rev_title(review):
        return review.find_element(By.CLASS_NAME, 'mb-xxsm').text.strip('"')

    def scrape_helpful(review):
        try:
            helpful = review.find_element(By.CLASS_NAME, 'common__EiReviewDetailsStyle__socialHelpfulcontainer').text
            if 'people found this review helpful' in helpful:
                res = int(helpful.split(' ')[0])
            else:
                res = 0
        except Exception:
            res = 0
        return res

    def scrape_pros(review):
        try:
            comments = review.find_elements(By.CLASS_NAME, 'v2__EIReviewDetailsV2__fullWidth')
            res = np.nan
            for r in comments:
                if r.find_element(By.TAG_NAME, 'p').text == 'Pros':
                    res = r.find_element(By.TAG_NAME, 'span').text
        except Exception:
            res = np.nan
        return res

    def scrape_cons(review):
        try:
            comments = review.find_elements(By.CLASS_NAME, 'v2__EIReviewDetailsV2__fullWidth')
            res = np.nan
            for r in comments:
                if r.find_element(By.TAG_NAME, 'p').text == 'Cons':
                    res = r.find_element(By.TAG_NAME, 'span').text
        except Exception:
            res = np.nan
        return res

    def scrape_advice(review):
        try:
            comments = review.find_elements(By.CLASS_NAME, 'v2__EIReviewDetailsV2__fullWidth')
            res = np.nan
            for r in comments:
                if r.find_element(By.TAG_NAME, 'span').get_attribute('data-test') == 'advice-management':
                    res = r.find_element(By.TAG_NAME, 'span').text
        except Exception:
            res = np.nan
        return res

    def scrape_overall_rating(review):
        try:
            ratings = review.find_element(By.CLASS_NAME, 'ratingNumber')
            res = float(ratings.text[:3])
        except Exception:
            res = np.nan
        return res

    def _scrape_subrating(i):
        try:
            r = review.find_element(By.CLASS_NAME, 'tooltipContainer').find_elements(By.TAG_NAME, 'li')
            srdiv = r[i].find_elements(By.TAG_NAME, 'div')
            srclass = srdiv[1].get_attribute('class')
            srclass = srclass.split(" ")
            res = v.index(srclass[0]) + 1
        except Exception:
            res = np.nan
        return res

    def scrape_work_life_balance(review):
        return _scrape_subrating(0)

    def scrape_culture_and_values(review):
        return _scrape_subrating(1)

    def scrape_diversity_and_inclusion(review):
        return _scrape_subrating(2)

    def scrape_career_opportunities(review):
        return _scrape_subrating(3)

    def scrape_comp_and_benefits(review):
        return _scrape_subrating(4)

    def scrape_senior_management(review):
        return _scrape_subrating(5)

    def _scrape_checkmark(i):
        try:
            r = review.find_element(By.CLASS_NAME, 'recommends').find_elements(By.CLASS_NAME, 'SVGInline-svg')
            att = r[i].get_attribute('class')
            if att == 'SVGInline-svg css-hcqxoa-svg d-flex-svg':
                res = 'mark'
            elif att == 'SVGInline-svg css-1h93d4v-svg d-flex-svg':
                res = 'line'
            elif att == 'SVGInline-svg css-1kiw93k-svg d-flex-svg':
                res = 'cross'
            elif att == 'SVGInline-svg css-10xv9lv-svg d-flex-svg':
                res = 'circle'
            else:
                res = np.nan
        except Exception:
            res = np.nan
        return res

    def scrape_recommends(review):
        return _scrape_checkmark(0)

    def scrape_approve_ceo(review):
        return _scrape_checkmark(1)

    def scrape_outlook(review):
        return _scrape_checkmark(2)

    def scrape_featured(review):
        try:
            review.find_element(By.CLASS_NAME, 'common__EiReviewDetailsStyle__newFeaturedReview')
            return True
        except selenium.common.exceptions.NoSuchElementException:
            return False

    funcs = [
        scrape_date,
        scrape_emp_title,
        scrape_location,
        scrape_status,
        scrape_rev_title,
        scrape_helpful,
        scrape_pros,
        scrape_cons,
        scrape_advice,
        scrape_overall_rating,
        scrape_work_life_balance,
        scrape_culture_and_values,
        scrape_diversity_and_inclusion,
        scrape_career_opportunities,
        scrape_comp_and_benefits,
        scrape_senior_management,
        scrape_recommends,
        scrape_outlook,
        scrape_approve_ceo,
        scrape_featured

    ]

    # mapping from subrating to integer value for 1,2,3,4,5 stars
    v = ['css-xd4dom', 'css-18v8tui', 'css-vl2edp', 'css-1nuumx7', 'css-s88v13']
    fdict = dict((s, f) for (s, f) in zip(SCHEMA, funcs))

    return fdict[field](review)


def extract_from_page(pending_count=9999):
    def expand_show_more(review):
        try:
            continue_link = review.find_element(By.CLASS_NAME, 'v2__EIReviewDetailsV2__newUiCta')
            continue_link.click()
        except Exception:
            pass

    def extract_review(review, pending_count=9999):
        try:
            author = review.find_element(By.CLASS_NAME, 'authorInfo')
        except:
            return None  # Account for reviews that have been blocked
        res = {}
        # import pdb;pdb.set_trace()
        for field in SCHEMA:
            res[field] = scrape(field, review, author)

        assert set(res.keys()) == set(SCHEMA)
        return res

    logger.info(f'Extracting reviews from page {page[0]}')

    res = pd.DataFrame([], columns=SCHEMA)

    reviews = browser.find_elements(By.CLASS_NAME, 'empReview')
    logger.info(f'Found {len(reviews)} reviews on page {page[0]}')

    # refresh page if failed to load properly, else terminate the search
    if len(reviews) < 1:
        browser.refresh()
        time.sleep(5)
        reviews = browser.find_elements(By.CLASS_NAME, 'empReview')
        logger.info(f'Found {len(reviews)} reviews on page {page[0]}')
        if len(reviews) < 1:
            valid_page[0] = False  # make sure page is populated

    for review in reviews:
        if pending_count == 0:
            break
        expand_show_more(review)
        data = extract_review(review, pending_count)
        if data != None:
            logger.info(f'Scraped data for "{data["review_title"]}"')
            res.loc[idx[0]] = data
            pending_count -= 1
        else:
            logger.info('Discarding a blocked review')
        idx[0] = idx[0] + 1

    if (args.max_date and (pd.to_datetime(res['date']).max() > args.max_date)) or \
            (args.min_date and (pd.to_datetime(res['date']).min() < args.min_date)):
        logger.info('Date limit reached, ending process')
        date_limit_reached[0] = True

    return res


def more_pages():
    try:
        current = browser.find_element(By.CLASS_NAME, 'selected')
        pages = browser.find_element(By.CLASS_NAME, 'pageContainer').text.split()
        if int(pages[-1]) != int(current.text):
            return True
        else:
            return False
    except selenium.common.exceptions.NoSuchElementException:
        return False


def go_to_next_page():
    logger.info(f'Going to page {page[0] + 1}')
    next_ = browser.find_element(By.CLASS_NAME, 'nextButton')
    ActionChains(browser).click(next_).perform()
    time.sleep(5)  # wait for ads to load
    page[0] = page[0] + 1


def no_reviews():
    return False
    # TODO: Find a company with no reviews to test on


def navigate_to_reviews():
    logger.info('Navigating to company reviews')

    browser.get(args.url)
    time.sleep(1)

    if no_reviews():
        logger.info('No reviews to scrape. Bailing!')
        return False

    reviews_cell = browser.find_element(By.XPATH, '//a[@data-label="Reviews"]')
    reviews_path = reviews_cell.get_attribute('href')

    # reviews_path = driver.current_url.replace('Overview','Reviews')
    browser.get(reviews_path)
    time.sleep(1)
    return True


def sign_in():
    logger.info(f'Signing in to {args.username}')

    url = 'https://www.glassdoor.co.in/profile/login_input.htm'
    browser.get(url)

    # import pdb;pdb.set_trace()

    email_field = browser.find_element("name", 'username')
    #email_field = browser.find_element("id", 'inlineUserEmail')
    #password_field = browser.find_element("id", 'password')
    submit_btn = browser.find_element("xpath", '//button[@type="submit"]')

    email_field.send_keys(args.username)
    password_field.send_keys(args.password)
    submit_btn.click()

    time.sleep(3)

    password_field = browser.find_element("id", 'password')
    submit_btn = browser.find_element("xpath", '//button[@type="submit"]')


def get_browser():
    logger.info('Configuring browser')
    chrome_options = wd.ChromeOptions()
    # if args.headless:
    #     chrome_options.add_argument('--headless')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('log-level=3')
    browser = wd.Chrome(options=chrome_options)
    return browser


def get_current_page():
    logger.info('Getting current page number')
    current = browser.find_element(By.CLASS_NAME, 'selected')
    return int(current.text)


def verify_date_sorting():
    logger.info('Date limit specified, verifying date sorting')
    ascending = urllib.parse.parse_qs(args.url)['sort.ascending'] == ['true']
    if args.min_date and ascending:
        raise Exception(
            'min_date required reviews to be sorted DESCENDING by date.')
    elif args.max_date and not ascending:
        raise Exception(
            'max_date requires reviews to be sorted ASCENDING by date.')


browser = get_browser()
page = [1]
idx = [0]
date_limit_reached = [False]
valid_page = [True]


def main():
    res = pd.DataFrame([], columns=SCHEMA)

    sign_in()
    config_data = pd.read_excel("config.xlsx")
    df = pd.DataFrame(config_data, columns=['company_url', 'no_of_reviews', 'min_date(optional)', 'max_date(optional)'])
    print(len(df))
    for index, row in df.iterrows():
        url = row["company_url"]
        n_reviews = row["no_of_reviews"]
        min_date = row["min_date(optional)"]
        max_date = row["max_date(optional)"]

        print(url)
        print(n_reviews)
        print(min_date)
        print(max_date)
        # parser.add_argument('-u', '--url',
        #                     help='URL of the company\'s Glassdoor landing page.',
        #                     default=url)

        args.url = url
        args.limit = n_reviews
        try:
            args.min_date = dt.datetime.strptime(str(min_date)[:-9], "%Y-%m-%d")
        except:
            pass
        try:
            args.max_date = dt.datetime.strptime(str(max_date)[:-9], "%Y-%m-%d")
        except:
            pass

        if args.max_date and args.min_date:
            raise Exception(
                'Invalid argument combination:\
                Both min_date and max_date specified.'
            )

        # parser.add_argument('-l', '--limit', default=n_reviews,
        #                    action='store', type=int, help='Max reviews to scrape')
        logger.info(f'Scraping up to {n_reviews} reviews.')

        browser.get(url)

        if not browser.current_url.__contains__("Reviews"):
            reviews_exist = navigate_to_reviews()
            if not reviews_exist:
                return

        if args.max_date or args.min_date:
            if args.min_date:
                args.url = args.url + "?sort.sortType=RD&sort.ascending=false&filter.iso3Language=eng"
            else:
                args.url = args.url + "?sort.sortType=RD&sort.ascending=true&filter.iso3Language=eng"
            browser.get(args.url)
            page[0] = get_current_page()
            logger.info(f'Starting from page {page[0]:,}.')
            time.sleep(1)
        else:
            browser.get(args.url)
            page[0] = get_current_page()
            logger.info(f'Starting from page {page[0]:,}.')
            time.sleep(1)

        company_name = browser.find_element(By.CLASS_NAME, "tightAll").text
        reviews_df = extract_from_page(n_reviews)
        res = res.append(reviews_df)

        # import pdb;pdb.set_trace()

        while more_pages() and \
                len(res) < n_reviews and \
                not date_limit_reached[0] and \
                valid_page[0]:
            go_to_next_page()
            try:
                pending_count = n_reviews - len(res)
                reviews_df = extract_from_page(pending_count)
                res = res.append(reviews_df)
            except:
                break

        company_name = company_name.replace("/", "-").replace("\\", "-")
        now = dt.datetime.now()
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S").replace("/", "-").replace(":", "_")
        logger.info(f'Writing {len(res)} reviews to file {company_name} {dt_string} ratings.xlsx')
        res.to_excel("{} {} ratings.xlsx".format(company_name, dt_string), index=False, encoding='utf-8')

        end = time.time()
        logger.info(f'Finished in {end - start} seconds')


if __name__ == '__main__':
    main()
