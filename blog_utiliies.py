import openai
import streamlit as st
from Bio import Entrez
import logging
from functools import wraps 
import random
from datetime import datetime,timedelta
# from openai import OpenAI
# from langchain.utilities import SerpAPIWrapper
# from langchain.agents import Tool
# from langchain.agents import AgentType
# from langchain.agents import initialize_agent
# from langchain.llms import OpenAI
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import os,sys


openapi_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = openapi_key
PUBMED_API_KEY=st.secrets["PUBMED_API_KEY"]
Entrez.email=st.secrets["email"]
serpapi_api_key=st.secrets["SERPAPI_API_KEY"]

# Setup the custom logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s:%(name)s:%(levelname)s:%(message)s:%(funcName)s')
file_handler = logging.FileHandler('mamsa_utlities.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

@st.cache_resource(hash_funcs={})
def installff():
    os.system('sbase install geckodriver')
    os.system('ln -s /home/appuser/venv/lib/python3.10.13/site-packages/seleniumbase/drivers/geckodriver /home/appuser/venv/bin/geckodriver')

installff()


#function to fetch article ids
def get_PMIDs_for_term(s_term):
    try:
        random_number = random.randint(15, 18)
        database = "pubmed"
        today_date = datetime.now().date()
        one_month_ago = today_date - timedelta(days=30)
        search_query = f'{s_term} AND ("{one_month_ago}"[PDAT] : "{today_date}"[PDAT])'
        search_results = Entrez.esearch(db=database, term=search_query, retmax=random_number, sort="relevance")
        record = Entrez.read(search_results)
        ids = record['IdList']
        return ids
    except Exception as ex:
        raise Exception(f"error {str(ex)}")


#function to fetch article abstract
def get_abstract_list_from_pmid_list(pmidlist):
    try:
        assert isinstance(pmidlist, list), "Input must be a list"
        
        scan_ids = []
        abstract_list = []
        
        with Entrez.efetch(db="pubmed", id=pmidlist, retmode="xml") as handle:
            records = Entrez.read(handle)
        
        for i, record in enumerate(records["PubmedArticle"]):
            if record["MedlineCitation"]["Article"].get("Abstract", None) is not None:
                abstract_list.append(str(record["MedlineCitation"]["Article"]["Abstract"]["AbstractText"]).replace('[', '').replace(']', '').replace("'", ""))
                scan_ids.append(pmidlist[i])

        return abstract_list, scan_ids
    except Exception as ex:
        raise Exception(f"Error: {str(ex)}")



#function tofetch article titles
def get_title_list_from_pmid_list(pmidlist):
    try:
        assert isinstance(pmidlist, list), "Input must be a list"
        
        title_list = []
        
        with Entrez.efetch(db="pubmed", id=pmidlist, retmode="xml") as handle:
            records = Entrez.read(handle)
        
        for record in records["PubmedArticle"]:
            if record["MedlineCitation"]["Article"].get("ArticleTitle", None) is not None:
                title_list.append(record["MedlineCitation"]["Article"]["ArticleTitle"])
        
        return title_list
    except Exception as ex:
        raise Exception(f"Error: {str(ex)}")


#function to create abstract summary
def generate_abstract_summary(all_texts):
    try:
        assert isinstance(all_texts, list), "Input must be a list"
        
        generated_list = []
        
        for i in range(len(all_texts)):
            prompt = f"""You are a text summarizer who is an expert at performing Extreme TLDR generation for given text. 
            Extreme TLDR is a form of extreme summarization, which performs high source compression, removes stop words, and
            summarizes the text while retaining meaning. The result is the shortest possible summary that retains all of 
            the original meaning and context of the text. The summary wording should be understood by a layman. The summary length should be at most 200 words.
            Text for Extreme TLDR generation: {all_texts[i]}
            Extreme TLDR: """
           
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert in generating summaries for legal documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            refined_text = response['choices'][0]['message']['content']
            generated_list.append(refined_text)
        
        return generated_list
    except Exception as ex:
        raise Exception(f"OpenAI error: {str(ex)}")




#function to extract keywords
def query_keywords(query):
    try:
        messages = [
            {"role": "system", "content": f"""You are trained to analyze user query and extract the main keyword from the query. The extracted keywords must accurately represent the essence of the entire query. Avoid adding any keywords in the response that are not explicitly present in the user's query. (*Response must not exceed two words)*. query: {query}."""},
            {"role": "user", "content": f"""You are trained to analyze user query and extract the main keyword from the query. The extracted keywords must accurately represent the essence of the entire query. Avoid adding any keywords in the response that are not explicitly present in the user's query. (*Response must not exceed two words)*. query: {query}."""}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.6
        )

        response_text = response.choices[0].message.content.strip().replace(",", "")
        print(response_text)
        return response_text
    except Exception as ex:
        raise Exception(f"OpenAI error: {str(ex)}")


#urls against pubmed ids
def generate_urls_from_pubmed_ids(id_list):
    try:
        assert isinstance(id_list, list), "Input must be a list"
        
        base_url = "https://pubmed.ncbi.nlm.nih.gov/"
        url_list = [base_url + str(id) + "/" for id in id_list]
        
        return url_list
    except Exception as ex:
        raise Exception(f"Error: {str(ex)}")



#scrapping function for full text against urls from pubmed
def article_full_text_scrapping(urls, id_lst):
    try:
        assert len(urls) == len(id_lst), "Length of URLs and ID list must be the same"
        
        generated_url_list = []
        scan_id_list = []

        for i in range(len(urls)):
            url = urls[i]
            response = requests.get(url)
            
            # Check if the request was successful
            response.raise_for_status()

            htmlContent = response.content
            soup = BeautifulSoup(htmlContent, 'html.parser')
            link = soup.find('a', class_='link-item pmc')
            
            if not link:
                link = soup.find('a', class_='link-item pmc dialog-focus')

            if link:
                target_link = link.get('href')
                
                if target_link[:42] == "https://www.ncbi.nlm.nih.gov/pmc/articles/":
                    generated_url_list.append(target_link)
                    scan_id_list.append(id_lst[i])

        return generated_url_list, scan_id_list
    except Exception as ex:
        raise Exception(f"error while extracting full text url.: {str(ex)}")

#scrapping for pmc website for pdf url
def pdf_url_scrapping(urls,id_lst):
    generated_url_list=[]
    scan_id_list=[]
    for i in range(len(urls)):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        # options.headless = True
        driver = webdriver.Firefox(options=options)
        driver.get(urls[i])
        try:
            loginBtn = driver.find_element(By.CLASS_NAME, "int-view")
            pdf_link = loginBtn.get_attribute('href')
            generated_url_list.append(pdf_link)
            scan_id_list.append(id_lst[i])
        except:
            continue
        driver.quit()
    return generated_url_list,scan_id_list
