import streamlit as st
from blog_utiliies import *
import openai
import streamlit as st
from Bio import Entrez
from functools import wraps 
from datetime import datetime


st.set_page_config(
    page_title="MRS",
    page_icon="📚"
)

openapi_key = st.secrets["OPENAI_API_KEY"]
openai.api_key = openapi_key
PUBMED_API_KEY=st.secrets["PUBMED_API_KEY"]
Entrez.email=st.secrets["email"]

if 'title' not in st.session_state:
    st.session_state['title'] = []
if 'abstract' not in st.session_state:
    st.session_state['abstract'] = []
if 'summary' not in st.session_state:
    st.session_state['summary'] = []
if 'ids' not in st.session_state:
    st.session_state['ids']=[]
if 'scan_ids' not in st.session_state:
    st.session_state['scan_ids']=[]
if 'keywords' not in st.session_state:
    st.session_state['keywords']=[]
if 'pubmed_url' not in st.session_state:
    st.session_state['pubmed_url']=[]
if 'pmc_scan_id' not in st.session_state:
    st.session_state['pmc_scan_id']=[]
if 'pmc_url' not in st.session_state:
    st.session_state['pmc_url']=[]
if 'pmc_pdf_url' not in st.session_state:
    st.session_state['pmc_pdf_url']=[]
if 'pmc_pdf_scan_ids' not in st.session_state:
    st.session_state['pmc_pdf_scan_ids']=[]






st.markdown(f"<h1 style='text-align: center; color:lightgreen;'>Research Synthesizer</h1>", unsafe_allow_html=True)
st.markdown(f"<h6 style='text-align: left; color:lightgreen;'>This research synthesizer tool assists in retrieving pertinent article titles, abstracts, and summaries related to your query</h6>", unsafe_allow_html=True)



st.write("\n")
prompt = st.text_input('Query:', key="input1")



article_title, article_abstract, article_summary=st.columns(3)

with article_abstract:
    if st.button("Proceed"):
        if prompt:
            with st.spinner("Working please wait"):
                st.session_state['keywords']=query_keywords(prompt)
                st.session_state['ids']=get_PMIDs_for_term(st.session_state['keywords'])
                print("--main ids---")
                print(st.session_state['ids'])
                st.session_state['pubmed_url']=generate_urls_from_pubmed_ids(st.session_state['ids'])
                print(st.session_state['pubmed_url'])
                st.session_state['pmc_url'],st.session_state['pmc_scan_id']=article_full_text_scrapping(st.session_state['pubmed_url'],st.session_state['ids'])
                print("ids after pmc url")
                print(st.session_state['pmc_scan_id'])

                st.session_state['pmc_pdf_url'],st.session_state['pmc_pdf_scan_ids']=pdf_url_scrapping(st.session_state['pmc_url'],st.session_state['pmc_scan_id'])
                print("ids after pdf")
                print(st.session_state['pmc_pdf_scan_ids'])

                st.session_state['abstract'],st.session_state['scan_ids']=get_abstract_list_from_pmid_list(st.session_state['pmc_pdf_scan_ids'])
                print("id after abstract")
                print(st.session_state['scan_ids'])
                # print(st.session_state['abstract'])
                st.session_state['title']=get_title_list_from_pmid_list(st.session_state['scan_ids'])
                # print(st.session_state['title'])
                st.session_state['summary']=generate_abstract_summary(st.session_state['abstract'])
                # print(st.session_state['summary'])



if st.session_state['summary'] and st.session_state['abstract'] and st.session_state['title']:
    i=1
    for title,abstract,summary,url in zip(st.session_state['title'],st.session_state['abstract'],st.session_state['summary'],st.session_state['pmc_pdf_url']):
                st.divider()
                st.markdown(f"<h1 style='text-align: center;'>Article {i}</h1>", unsafe_allow_html=True)
                article_data = {
                "article_title": title,
                "article_abstract": abstract,
                "article_summary": summary,
                "article_pdf_link":url}
                st.subheader(f"Title:")
                st.write(article_data['article_title'])
                st.subheader(f"Abstract:")
                st.write(str(article_data['article_abstract']))
                st.subheader(f"Summary:")
                st.write(article_data['article_summary'])
                st.subheader("Full article view")
                st.markdown(f'<a href={url} target="_blank">Click here for full view</a>', unsafe_allow_html=True)
                i+=1

