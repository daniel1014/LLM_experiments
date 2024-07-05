## This was just a developing file to test the Cohere API and Streamlit integration.

import streamlit as st
import cohere
from dotenv import dotenv_values
import general_utils
import cohere_utils
from annotated_text import annotated_text

# App title
st.set_page_config(
    page_title="News Scraping",
    page_icon="assets/page_icon.png",
)

config = dotenv_values(".env")

general_utils.add_logo("assets/logo.png")

citation_info = st.empty()
with st.sidebar:
    st.title('🤖 AI-powered Chatbot')
    if 'COHERE_API_KEY' in config:
        cohere_api = config['COHERE_API_KEY']
    elif 'COHERE_API_KEY' in st.secrets:
        st.success('API key already provided!', icon='✅')
        cohere_api = st.secrets['COHERE_API_KEY']
    else:
        cohere_api = st.text_input('Enter Cohere API token:', type='password')
        if not (len(cohere_api)==40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    tab1, tab2 = st.tabs(["Basic", "Advanced"])
    with tab1:
        datasource_radio = st.radio("External Data Source", ["Static News", "Web Search", "Local File"],
        captions = ["Utilise the scrapped news articles to answer your question", 
                    "Leverage a dynamic web search engine to enrich the chatbot's response",
                    "Upload a PDF or TXT document to be used as an external datasource."],
        help='''Choose data source for the chatbot's response: Static news articles, dynamic web search, or a local file. 
        For instance, when 'Web Search' is specified, the model's reply will be enriched dynamically with information found by web search.''')
        
        citation_radio = st.radio("Include Citations", ["No", "Yes"],
        help="Enable to include highlighted citations and references in the chatbot's response."
        )
        if citation_radio == "Yes":
            citation_info.info('Citations will be included in the chatbot response.')
        if datasource_radio == "Local File":
            uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=['pdf', 'txt'], )
            if uploaded_file:
                st.write(f'File uploaded: {uploaded_file.name}')
    with tab2:
        st.subheader('Advanced settings')
        preamble_template= st.text_area('Preamble Template', '''
        ## Task and Context
        You are a helpful, respectful and honest assistant. Please summarize the salient points of the text and do so in a flowing high natural language quality text. 
        Use bullet points where appropriate.

        ## Style Guide
        Use British spelling of words, and be professional.
        ''')


st.title('AI-powered Chatbot')

if 'messages' not in st.session_state:
    st.session_state.messages = [{'role': 'CHATBOT', 'message': 'Hello! How can I help you today?'}]

for message in st.session_state.messages:
    st.chat_message(message['role']).write(message['message'])

preamble_template='''

## Task and Context
You are a helpful, respectful and honest assistant. Please summarize the salient points of the text and do so in a flowing high natural language quality text. 
Use bullet points where appropriate.

## Style Guide
Use British spelling of words, and be professional.
'''


def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "message": "Hi how may I assist you? Please ask me any question about your scrapped news articles!"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

prompt = st.chat_input('Enter your message:')
if prompt:
    if not cohere_api:
        st.info('Please enter your Cohere API key to continue.')
        st.stop()
    st.chat_message('USER').write(prompt)
    with st.chat_message('CHATBOT'):
        with st.spinner('Thinking...'):
            Client = cohere.Client(cohere_api)
            response = Client.chat_stream(message=prompt, connectors=[{"id": "web-search","continue_on_failure": False}],
                                                                preamble = preamble_template)
            
            # Print the chatbot response, citations, and documents
            citations = []
            cited_documents = []
            # Display response
            placeholder = st.empty()
            full_response = ''
            for event in response:
                if event.event_type == "text-generation":
                    full_response+= str(event.text)
                    placeholder.markdown(full_response)
                elif event.event_type == "citation-generation":
                    citations.extend(event.citations)
                elif event.event_type == "search-results":
                    cited_documents = event.documents

            text_citated = cohere_utils.annotate_citations(full_response, citations)
            annotated_text(text_citated)
            # st.write(response.text)
            st.markdown('#### Relevant Articles:')
            for doc in sorted(cited_documents, key=lambda d: d['id']):
                st.write(f"[{doc['id'][11:]}] [{doc['title']}]({doc['url']})")
            st.session_state.messages.append({'role': 'USER', 'message': prompt})
            st.session_state.messages.append({'role': 'CHATBOT', 'message': full_response})
            # for x in response:
            #     print(x)



