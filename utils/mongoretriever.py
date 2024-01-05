from langchain.schema import BaseRetriever
from langchain.callbacks.manager import CallbackManagerForRetrieverRun
from langchain.vectorstores import MongoDBAtlasVectorSearch
from langchain.schema import Document
from pydantic import Field
from attrs import define
from typing import  List
from pymongo import MongoClient

@define(kw_only=True)
class MongoDBVector:
    uri: str
    db_name: str
    collection_name: str
    index_name: str

    def get_vector_db(self, embeddings):

        # initialize MongoDB python client
        client = MongoClient(self.uri)
        collection = client[self.db_name][self.collection_name]

        vectordb = MongoDBAtlasVectorSearch(
            embedding=embeddings,
            index_name=self.index_name,
            collection=collection, 
        )

        return vectordb


class MongoDBExtendedRetriever(BaseRetriever):
    vectorstore: MongoDBAtlasVectorSearch
    search_type: str = "similarity"
    """Type of search to perform. Defaults to "similarity"."""
    search_kwargs: dict = Field(default_factory=dict)
 
    class Config:
        arbitrary_types_allowed = True
 
    def combine_metadata(self, doc) -> str:
        metadata = doc.metadata
        content = ("Item Name: " + metadata["item_name"] + ". " +
           "Item Description: " + metadata["bullet_point"] + ". " +
           "Item Keywords: " + metadata["item_keywords"] + ".")
        return content, metadata
    
    def combine_metadata_c(self, doc) -> str:
        #print(doc)
        metadata = {
            "Item Name": doc["item_name"],
             "Item Keywords": doc["bullet_point"]
        }
        content = ("Item Name: " + doc["item_name"] + ". " +
           "Item Description: " + doc["bullet_point"] + ". " +
           "Item Keywords: " + doc["item_keywords"] + ".")
        return content, metadata
 
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> List[Document]:
        
        #print('In fuction: ',self.vectorstore._index_name, query)
        docs_list = []
        mongo_query = [
            {
                "$search": {
                    "index": self.vectorstore._index_name,
                    "knnBeta": {
                        "vector": self.vectorstore.embeddings.embed_query(query),
                        "path": "embedding",
                        "k": 10,
                    }
                }
            }
        ]

        #docs = self.vectorstore._collection.aggregate(mongo_query)
        docs =self.vectorstore.similarity_search(query, **self.search_kwargs)

        #print('Docs: ',docs)

        for doc in docs:
            content, metadata = self.combine_metadata(doc)
            docs_list.append(Document(
                page_content=content,
                metadata=metadata
            ))
 
        return docs_list