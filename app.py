import streamlit as st
import json
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import plotly.express as px
from annotated_text import annotated_text
import re
import uuid

with st.sidebar:
    st.markdown(
        """
    <style>
        [data-testid=stSidebar] [data-testid=stImage]{
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True
    )
    st.image("https://www.onepointltd.com/wp-content/uploads/2020/03/inno2.png",  width=100)
    st.markdown("<h1 style='text-align: center; color: black;'>Legal Analytics</h1>",
                unsafe_allow_html=True)

    with open('creds.json') as f:
        json_file = f.read()
    creds = json.loads(json_file)
    apikey = creds['apikey']
    url = creds['url']

    authenticator = IAMAuthenticator(apikey)
    discovery = DiscoveryV2(version='2019-11-22', authenticator=authenticator)
    discovery.set_service_url(url)
    discovery.set_disable_ssl_verification(True)
    projects = discovery.list_projects()
    projectdict = {project['name']: project['project_id']
                   for project in projects.result['projects']}

    project = st.selectbox("Select a Project", projectdict.keys())

    collections = discovery.list_collections(project_id=projectdict[project])
    collectiondict = {collection['name']: collection['collection_id']
                      for collection in collections.result['collections']}
    collection = st.selectbox("Select a Collection", collectiondict.keys())

    choice = st.radio("Navigation", [
                      'Model Clauses', 'NLP Visualization', 'JSON Out', 'Document Management'])
    st.info("Watson Discovery is evolving beyond an enterprise search solution, and into to a powerful platform providing both document and language understanding to uncover hidden insights employees need when working on complex processes")

if choice in ['Model Clauses', 'NLP Visualization', 'JSON Out']:
    query = st.text_input("Pass your input here")

if choice == 'Model Clauses':
    st.title('Analyse Clauses')

    if query:
        query_result = discovery.query(
            project_id=projectdict[project],
            collection_ids=[collectiondict[collection]],
            natural_language_query=query, return_=['categories']).get_result()

        st.info(f'{query_result["matching_results"]} results found')

        for document in query_result['results']:
            try:
                raw_result = document['document_passages'][0]['passage_text']
                res = re.split(r"(\<em>)|(\</em>)", raw_result)

                annotated = []
                line_iter = enumerate(res)
                for idx, x in line_iter: 
                    if x not in ["<em>", "</em>", None]:
                        annotated.append(x)
                    if x == "<em>":
                        annotation = (res[idx+2], "match")
                        annotated.append(annotation)
                        line_iter.__next__() 
                        line_iter.__next__() 

                with st.expander(raw_result[:100].replace('<em>', '').replace('</em>', '')):
                    annotated_text(*annotated)
                    st.write('---------------------------------------------------------')
                    col1, col2, col3, col4 = st.columns((4,2,1,1))
 
                    with col1: 
                        st.write('Confidence:', document['result_metadata']['confidence'])
                    with col2: 
                        st.write('**Was this helpful?**') 
                    with col3:
                        st.button('👍 Yes', key=uuid.uuid1())
                    with col4: 
                        st.button('👎 No', key=uuid.uuid1())                    

            except Exception as e:
                pass

if choice == 'NLP Visualization':
    st.title('Visualize Your Documents')
    if query:
        query_result = discovery.query(
            project_id=projectdict[project],
            collection_ids=[collectiondict[collection]],
            natural_language_query=query, return_=['categories']).get_result()

        for aggregation in query_result['aggregations']:
            try:
                aggkeys = [res['key'] for res in aggregation['results']]
                aggnum = [res['matching_results']
                          for res in aggregation['results']]
                chart = px.bar(y=aggnum, x=aggkeys,
                               title=aggregation['name'].title())
                st.plotly_chart(chart)
            except Exception as e:
                pass

if choice == 'Document Management':
    st.file_uploader("Upload a new document to Watson Discovery")

if choice == 'JSON Out':
    with open('data.json', 'r') as f:
        data = json.load(f)
    st.title('Displaying Watson JSON')
    st.json(data)
