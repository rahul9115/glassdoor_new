'''
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
'''
import time
import pandas as pd
from argparse import ArgumentParser
import argparse
import logging
import logging.config
from selenium import webdriver as wd
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
import selenium
import numpy as np
#from schema import SCHEMA - for final excel
import json
import urllib
import datetime as dt
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
start = time.time()
def get_browser():
    logger.info('Configuring browser')
    chrome_options = wd.ChromeOptions()
    browser = wd.Chrome()
    return browser
def sign_in():
    logger.info(f'Signing in')
    time.sleep(2)
    url = 'https://www.glassdoor.co.in/index.htm'
    browser.get(url)
    signin_button = browser.find_element_by_xpath('//*[@id="SiteNav"]/nav/div[2]/div/div/div/button')
    signin_button.click()
    email_field = browser.find_element_by_xpath('//*[@id="modalUserEmail"]')
    password_field = browser.find_element_by_xpath('//*[@id="modalUserPassword"]')
    submit_btn = browser.find_element_by_xpath('//*[@id="LoginModal"]/div/div/div[2]/div[2]/div[2]/div/div/form/div[3]/button')
    time.sleep(2)
    email_field.send_keys("reuben.thomas@yahoo.co.in")
    password_field.send_keys("remindme")
    submit_btn.click()
    time.sleep(2)
    #Temporary Link Embedded
    #browser.get("https://www.glassdoor.co.in/Reviews/LTI-Reviews-E30653.htm")
    logger.info(f'Login Succesful')
def search_company():
    logger.info('Searching into Company')
    company_name = "LTI"
    time.sleep(3)
    company_tab_selection = browser.find_element_by_xpath('//*[@id="SiteNav"]/nav[2]/div/div/div[2]/div[2]/div[1]/div/a/span/div')
    company_tab_selection.click()
    time.sleep(2)
    company_to_search = browser.find_element_by_xpath('//*[@id="sc.keyword"]')
    #For dynamic, we will take search Input here
    company_to_search.send_keys("lti")
    time.sleep(2)
    search_button = browser.find_element_by_xpath('//*[@id="scBar"]/div/button')
    search_button.click()
    overall_rating = []
    companies = browser.find_elements(By.CLASS_NAME, "single-company-result")
    index = 1
    for company in companies:
        print(str(index) + ". " + company.find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a").text)
        index += 1
    choice = int(input("Enter index no to select company: ")) - 1
    selected_company_link = companies[choice].find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME,"a").get_attribute("href")
    #driver.find_element(By.XPATH, ".//h1[@class='wsj-article-headline'']")
    #browser.find_element(By.ID, "SignInButton").click()
    browser.get(selected_company_link)
    browser.get(browser.find_element(By.CLASS_NAME, "reviews").get_attribute("href"))
    reviews = browser.find_elements(By.CLASS_NAME, "empReview")
    print(reviews)
    for review in reviews:
        overall_rating.append(review.find_element(By.CLASS_NAME, "ratingNumber").get_attribute("innerText"))

    print(overall_rating)



browser = get_browser()
sign_in()
search_company()