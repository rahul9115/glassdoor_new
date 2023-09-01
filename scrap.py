from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC




def scrap(company_name):
    driver = webdriver.Chrome()

    products=[] #List to store name of the product
    prices=[] #List to store price of the product
    ratings=[] #List to store rating of the product

    company_name = company_name.strip()
    company_name = company_name.replace(" ", "-")

    driver.get("https://www.glassdoor.co.in/Reviews/"+company_name+"-reviews-SRCH_KE0,"+str(len(company_name))+".htm")
    companies = driver.find_elements(By.CLASS_NAME, "single-company-result")
    #companies = driver.find_elements(by=By.CSS_SELECTOR, value=".single-company-result")

    html_content = driver.page_source
    # Parse the html content
    soup = BeautifulSoup(html_content, "html.parser")
    #print(soup.prettify())  # print the parsed data of html

    #content = driver.page_source
    #soup = BeautifulSoup(content, "html.parser")
    '''
    for company in soup.find_all("div", class_="single-company-result"): #soup.select("div.single-company-result"):
        print("\n")
        print(company.text)
        print(company.find("h2").find("a").innerText)
    '''
    index = 1
    for company in companies:
        print(str(index) + ". " +company.find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a").text)
        index+=1

    choice = int(input("Enter index no to select company: "))-1
    selected_company_link = companies[choice].find_element(By.TAG_NAME, "h2").find_element(By.TAG_NAME, "a").get_attribute("href")
    driver.get(selected_company_link)
    




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