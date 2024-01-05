import boto3
from langchain.embeddings import BedrockEmbeddings
from dotenv import load_dotenv
from utils.mongoretriever import MongoDBExtendedRetriever, MongoDBVector
import os

class ShoppingAssistant():
    def __init__(self, index_name, logger= None):
        load_dotenv()
        self.boto3_bedrock  = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-west-2",
        )
        self.logger = logger
        self.br_embeddings = BedrockEmbeddings(client=self.boto3_bedrock, model_id='amazon.titan-embed-text-v1')
        self.domain_index = index_name
        self.mdb_endpoint = f"mongodb+srv://{os.environ.get('MDB_USERNAME')}:{os.environ.get('MDB_PASSWORD')}@{os.environ.get('MDB_HOST')}/?retryWrites=true&w=majority"
        self.mdb_username = os.environ.get('MDB_USERNAME')
        self.mdb_password = os.environ.get('MDB_PASSWORD')
        self.mdb_collection = os.environ.get('MDB_COLLECTION')
        self.mdb_database = os.environ.get('MDB_DATABASE')
        self.retriever = self.get_retriever( search_kwargs={"k": 7})
        
    
    def get_retriever(self, search_kwargs):
        self.logger.info('In retriever')

        #print(self.mdb_endpoint , self.mdb_database, self.mdb_collection, self.domain_index)

        vector = MongoDBVector(
            uri= self.mdb_endpoint,
            db_name = self.mdb_database,
            collection_name = self.mdb_collection,
            index_name = self.domain_index
         )

        vectordb = vector.get_vector_db(embeddings = self.br_embeddings)     

        retriever = MongoDBExtendedRetriever(vectorstore= vectordb, search_type='similarity', search_kwargs={"k": 7})

        print('Got retriever')
        self.logger.info('Got retriever')

        return retriever
