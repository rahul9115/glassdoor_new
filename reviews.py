from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.common.by import By

def scrap(company_name):
    driver = webdriver.Chrome()

    products = []  # List to store name of the product
    prices = []  # List to store price of the product
    overall_rating = []  # List to store rating of the product

    company_name = company_name.strip()
    company_name = company_name.replace(" ", "-")

    driver.get(
        "https://www.glassdoor.co.in/Reviews/" + company_name + "-reviews-SRCH_KE0," + str(len(company_name)) + ".htm")
    companies = driver.find_elements(By.CLASS_NAME, "single-company-result")


    index = 1
    for company in companies:
        print(str(index) + ". " + company.find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a").text)
        index += 1

    choice = int(input("Enter index no to select company: ")) - 1
    selected_company_link = companies[choice].find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME,
                                                                                           "a").get_attribute("href")

    #driver.find_element(By.XPATH, ".//h1[@class='wsj-article-headline'']")
    driver.find_element(By.ID, "SignInButton").click()

    driver.get(selected_company_link)
    driver.get(driver.find_element(By.CLASS_NAME, "reviews").get_attribute("href"))
    reviews = driver.find_elements(By.CLASS_NAME, "empReview")
    print(reviews)

    for review in reviews:
        overall_rating.append(review.find_element(By.CLASS_NAME, "ratingNumber").get_attribute("innerText"))

    print(overall_rating)

company_name = input("Enter name of the company for which you want to scrap data: ")
scrap(company_name)

'''
for a in soup.findAll('a',href=True, attrs={'class':'_31qSD5'}):
name=a.find('div', attrs={'class':'_3wU53n'})
price=a.find('div', attrs={'class':'_1vC4OE _2rQ-NK'})
rating=a.find('div', attrs={'class':'hGSR34 _2beYZw'})
products.append(name.text)
prices.append(price.text)
ratings.append(rating.text) 

#df = pd.DataFrame({'Product Name':products,'Price':prices,'Rating':ratings}) 
#df.to_csv('products.csv', index=False, encoding='utf-8')
'''