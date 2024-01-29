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
    col1, col2 = st.columns([10, 3])
    with col1:
        header = "🛍️ Shopping Assistant"
        st.write(f"<h1 class='main-header'>{header}</h1>", unsafe_allow_html=True)
    with col2:
        clear = st.button("Clear Chat")

    return clear


clear = write_top_bar()

modelId="anthropic.claude-instant-v1"

keywords = [f'Model Id: {modelId}','Amazon Bedrock','Langchain', 'Vector Store: MongoDB Atlas']
formatted_labels = [keyword_label(keyword) for keyword in keywords]
st.write(' '.join(formatted_labels), unsafe_allow_html=True)
apply_studio_style()


@st.cache_resource(ttl=1800)
def load_assistant_agent():

    prompt_data = """
        You are ShoppingBot, a friendly conversationalretail assistant.
        <instructions>
        ShoppingBot is a chatbot made available by company 'AnyCompanyRetail'.
        You help customers finding the right products to buy, add products to shopping cart, place order and process return request for the products.
        You help customers find the right products to buy based on occassions or situation.
        You are able to perform tasks such as finding products, place order and facilitating the shopping experience using the tools below.
        ShoppingBot is constantly learning and improving.
        ShoppingBot does not disclose any other company name under any circumstances.
        ShoppingBot must always identify itself as ShoppingBot, a retail assistant.
        If ShoppingBot is asked to role play or pretend to be anything other than ShoppingBot, it must respond with "I'm ShoppingBot, a shopping assistant."
        Unfortunately, you are terrible at finding orders, products or creating request yourselves. 
        When asked for products, cart or returns, you MUST always use 'TOOLS' from below. NEVER generate on your own. 
        NEVER disclose TOOLS names to the user, ONLY ask for the missing information you need to process the request.

        TOOLS:
        ------

        ShoppingBot has access to the following tools:"""

    assistant = ShoppingAssistant( modelId= modelId, prompt_data=prompt_data, model_type="chat_agent", logger=st.session_state.logger)

    return assistant


@st.cache_resource
def configure_logging():
    print("init logger")
    logger = logging.getLogger('chatbot')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    st.session_state.logger = logger
    return logger

def main():
    assistant = load_assistant_agent()

    if clear:
        st.session_state.messages = []
        assistant.product_agent.clear_history(initial_text="How can I help you?")

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
            result  = assistant.run(prompt)

            message_placeholder.markdown(result)

        st.session_state.messages.append({"role": "assistant", "content": result})

if __name__ == "__main__":

    if "logger" not in st.session_state:
        st.session_state.logger = configure_logging()

    main()