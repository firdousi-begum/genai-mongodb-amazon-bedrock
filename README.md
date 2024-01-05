# amazon-bedrock-genai-chatbot

This repository contains code samples for a chatbot using Amazon Bedrock, LangChain & OpenSearch.

### Gain Model Access from Amazon Bedrock Console

Visit the [Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) for instructions on gaining model access. For Claude access, use the `us-east-1` or `us-west-2` region. 

> NOTE: This codebase uses the region `us-west-2`. Please update the region in [langchain.py](utils/langchain.py) and [shopping_agent.py](utils/shopping_agent.py) if using another region.

### Install Required Packages

Open your terminal and run:

```bash
pip install -r requirements.txt
```

### Create MongoDB vector and embed e-commerce product details
1. Create MongoDB instaance and not down the host, username, and password.

2. Create a .env file in the root directory and add the following environment variables:

```env
MDB_HOST="https://xxxxxx.mongodb.net"
MDB_USERNAME="REPLACE_WITH_YOUR_USERNAME"
MDB_PASSWORD="REPLACE_WITH_YOUR_PASSWORD"
```
3. Follow the notebook [shopping-bot.ipynb](notebook/shopping-bot.ipynb) to download product data and embed and store in MongoDB Vector

4. Update .env file in the root directory and add the following collection and database names as well:

```env
MDB_HOST="https://xxxxxx.mongodb.net"
MDB_USERNAME="REPLACE_WITH_YOUR_USERNAME"
MDB_PASSWORD="REPLACE_WITH_YOUR_PASSWORD"
MDB_COLLECTION="REPLACE_WITH_YOUR_COLLECTION"
MDB_DATABASE="REPLACE_WITH_YOUR_DATABASE"
```

3. Run the following command:

```bash
streamlit run chatbot_rag.py
```

### Start chatting
While chatting, see your terminal window to see how the chain is running.
> NOTE: Set verbose=False for chain `ConversationalRetrievalChain` in the file [langchain.py](utils/langchain.py) if you dont want to see detail output.