import time
import os
import streamlit as st
import uuid
import logging
from utils.langchain import LangChainAssistant
from utils.shopping_agent import ShoppingAssistant
from utils.studio_style import apply_studio_style
from utils.studio_style import keyword_label

if "user_id" in st.session_state:
    user_id = st.session_state["user_id"]
else:
    user_id = str(uuid.uuid4())
    st.session_state["user_id"] = user_id


def write_top_bar():
    col1, col2, col3, col4 = st.columns([1.5,2, 10, 3])
    with col1:
        st.image("images/amazon-bedrock-logo.svg", width=50)
    with col2:
        st.image("images/mongodb-atlas.png")
    with col3:
        header = "Product Search Chatbot"
        st.write(f"<h3 class='main-header'>{header}</h3>", unsafe_allow_html=True)
    with col4:
        clear = st.button("Clear Chat")

    return clear


clear = write_top_bar()

modelId="anthropic.claude-v2"

keywords = [f'Model Id: {modelId}','Amazon Bedrock','Langchain', 'Vector Store: MongoDB Atlas']
formatted_labels = [keyword_label(keyword) for keyword in keywords]
st.write(' '.join(formatted_labels), unsafe_allow_html=True)
apply_studio_style()


@st.cache_resource(ttl=1800)
def load_assistant():
    prompt_data = """You are ShoppingBot, a friendly conversationalretail assistant.
    ShoppingBot is a chatbot made available by company 'AnyCompanyRetail'.
    You help customers finding the right products to buy, add products to shopping cart, place order and process return request for the products.
    You should ALWAYS answer user inquiries based on the context provided and avoid making up answers.
    If you don't know the answer, simply state that you don't know. Do NOT make answers and hyperlinks on your own.

    <context>
    {context}
    </context
    
    <question>{question}</question>"""
    
    assistant = LangChainAssistant(modelId=modelId, retriever= get_retriver(), prompt_data= prompt_data)

    return assistant

@st.cache_resource(ttl=1800)
def get_retriver():
    mdb_assistant = ShoppingAssistant(index_name = "products-metadata", logger=st.session_state.logger)
    return mdb_assistant.retriever

@st.cache_resource
def configure_logging():
    print("init logger")
    logger = logging.getLogger('chatbot')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    st.session_state.logger = logger
    return logger

def main():
    assistant = load_assistant()

    if clear:
        st.session_state.messages = []
        assistant.clear_history()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            # prompt = prompt_fixer(prompt)
            result  = assistant.chat_doc(prompt)

            message_placeholder.markdown(result)

        st.session_state.messages.append({"role": "assistant", "content": result})

if __name__ == "__main__":

    if "logger" not in st.session_state:
        st.session_state.logger = configure_logging()

    main()