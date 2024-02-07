# amazon-bedrock-genai-chatbot

This repository contains code samples for a chatbot using Amazon Bedrock, LangChain & MongpDB Atlas Vector Search.

### Gain Model Access from Amazon Bedrock Console

Visit the [Amazon Bedrock documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) for instructions on gaining model access. For Claude access, use the `us-east-1` or `us-west-2` region. 

> NOTE: This codebase uses the region `us-west-2`. Please update the region in the `.env` file if using another region.

### Create MongoDB instance 

Create a MongoDB instance by following the instructions in [the documentation](https://www.mongodb.com/basics/create-database).  Note down the host, username, and password.

> &#x26a0;&#xfe0f; **Pay attention to the network setup. If you are using SageMaker studio to go along with this tutorial, you will need to expose the MongoDB instance to the internet.**:

### Populate instance with embeddings

1. Create a `.env` file in the root directory and add the following environment variables:

```env
MDB_HOST="REPLACE_WITH_HOST_NAME.mongodb.net"
MDB_USERNAME="REPLACE_WITH_YOUR_USERNAME"
MDB_PASSWORD="REPLACE_WITH_YOUR_PASSWORD"
```

2. Follow the notebook [shopping-bot.ipynb](notebook/shopping-bot.ipynb) to download product data and embed and store in MongoDB Vector

3. Update the `.env` file in the root directory and add the collection and database names as well:

```env
MDB_HOST="REPLACE_WITH_HOST_NAME.mongodb.net"
MDB_USERNAME="REPLACE_WITH_YOUR_USERNAME"
MDB_PASSWORD="REPLACE_WITH_YOUR_PASSWORD"
MDB_COLLECTION="REPLACE_WITH_YOUR_COLLECTION"
MDB_DATABASE="REPLACE_WITH_YOUR_DATABASE"
```

### Run streamlit application

```bash
streamlit run chatbot_rag.py
```

### Start chatting
While chatting, check your terminal window to see how the chain is running.
> NOTE: Set verbose=False for chain `ConversationalRetrievalChain` in the file [langchain.py](utils/langchain.py) if you dont want to see detail output.