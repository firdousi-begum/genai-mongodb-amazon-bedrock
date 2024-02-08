import boto3
from langchain.embeddings import BedrockEmbeddings
from dotenv import load_dotenv
from utils.mongoretriever import MongoDBExtendedRetriever, MongoDBVector
from utils.langchain import LangChainAssistant
from langchain.tools import tool
from langchain.tools import StructuredTool
import os

class ShoppingAssistant():
    def __init__(self,modelId,prompt_data, model_type="chat_doc", logger= None):
        load_dotenv()
        self.boto3_bedrock  = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-west-2",
        )
        self.logger = logger
        self.modelId = modelId
        self.br_embeddings = BedrockEmbeddings(client=self.boto3_bedrock, model_id='amazon.titan-embed-text-v1')
        self.domain_index = "products-metadata"
        self.mdb_endpoint = f"mongodb+srv://{os.environ.get('MDB_USERNAME')}:{os.environ.get('MDB_PASSWORD')}@{os.environ.get('MDB_HOST')}/?retryWrites=true&w=majority"
        self.mdb_username = os.environ.get('MDB_USERNAME')
        self.mdb_password = os.environ.get('MDB_PASSWORD')
        self.mdb_collection = os.environ.get('MDB_COLLECTION')
        self.mdb_database = os.environ.get('MDB_DATABASE')
        self.retriever = self.get_retriever( search_kwargs={"k": 7})
        self.product_qa = self.get_product_qa()
        self.tools = self.get_tools()
        self.product_agent = LangChainAssistant(modelId=modelId, bedrock_client=self.boto3_bedrock, retriever= self.retriever, prompt_data= prompt_data, model_type= model_type, tools=self.tools)

    def run(self, query):
        return self.product_agent.run(query) 
    
    def clear_history(self):
        return self.product_agent.clear_history()

    def get_product_qa(self):
        prompt_data = """You are ShoppingBot, a retail shopping assistant who helps in finding products from catalog.
        Use the following context including product names, descriptions, and keywords to show the shopper whats available, help find what they want, and answer any questions.
        You should answer user inquiries based on the context provided and avoid making up answers.
        If you don't know the answer, simply state that you don't know. Do NOT make answers and hyperlinks on your own.

        <context>
        {context}
        </context

        <question>{question}</question>"""
        modelId="anthropic.claude-instant-v1"
        assistant = LangChainAssistant(modelId=modelId, bedrock_client=self.boto3_bedrock, retriever= self.retriever, prompt_data= prompt_data, model_type= "chat_doc")

        return assistant.model
    
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

    def get_tools(self):

        # @tool(return_direct=True)
        # @tool
        # def retrieve_products(query: str) -> str:
        #     """Find and suggest products from catalog based on users needs or preferences in the query. 
        #     Requires full 'input' question as query.
        #     Useful for when a user is searching for products, asking for details,
        #     or want to buy some product.
        #     Useful for finding products with name, description, color, size, weight and other product attributes.
        #     Return the output without processing further.
        #     """
        #     res = self.product_qa(query)
        #     output = res['result']
        #     # documents = self.product_retriever.get_relevant_documents(query)
        #     # print(documents)
        #     # output = ''
        #     # for doc in documents:
        #     #     output = f"{output}{doc.page_content}\n"
        #     return output
        
        @tool
        def retrieve_products(query: str) -> str:
            """Find and suggest products from catalog based on users needs or preferences in the query. 
            Requires full 'input' question as query.
            Useful for when a user is searching for products, asking for details,
            or want to buy some product.
            Useful for finding products with name, description, color, size, weight and other product attributes.
            Return the output without processing further.
            """
            
            documents = self.retriever.get_relevant_documents(query)
            print(documents)
            output = ''
            for doc in documents:
                output = f"{output}{doc.page_content}\n"
            return output

        # @tool
        # def retrieve_products(query: str) -> str:
        #     """Find and suggest products from catalog based on users needs or preferences in the query. 
        #     Requires full 'input' question as query.
        #     Useful for when a user is searching for products, asking for details,
        #     or want to buy some product.
        #     Useful for finding products with name, description, color, size, weight and other product attributes.
        #     Return the output without processing further.
        #     """
        #     output = self.product_qa.run(query)
        #     # documents = self.product_retriever.get_relevant_documents(query)
        #     # print(documents)
        #     # output = ''
        #     # for doc in documents:
        #     #     output = f"{output}{doc.page_content}\n"
        #     return output
        
        @tool(return_direct=True)
        def add_product_to_cart(product: str) -> str:
            """Adds product to shopping cart.
            Use this to tool when user wants to buy a product or ask to add product to cart. 
            Return the output without processing further.
            """
            
            output = f"Added '{product}' to cart."
            return output
        
        # @tool(return_direct=True)
        @tool
        def get_orders_for_return(query: str) -> str:
            """Gets list of orders available for return request.
            Use this tool to get list of orders when user wants to return items or want to create return request.
            Return orderId and Items and ask user to 'Select items for return & reason for return from the list'.
            """
            try:
                #result = self.db.getItemsByStatus("delivered")
                result = [
                    {
                        "orderId": "OT1002",
                        "items": [
                            {
                                "name": "Knitted Cap",
                                "price": "100",
                                "quantity": "2"
                            }
                        ]
                    },
                    {
                        "orderId": "OT1003",
                        "items": [
                            {
                                "name": "Blue Shirt",
                                "price": "300",
                                "quantity": "1"
                            }
                        ]
                    }
                ]

                orders = ''

                for order in result:
                    format = "\n ".join([f"- {item['name']}, Price: {item['price']},  Qty: {item['quantity']}" for item in order['items']])
                    orders = f"{orders}OrderId: {order['orderId']} \n {format} \n\n"

                
                reasons = [
                'Low Quality',
                'Large Size',
                'Small Size',
                'Other - Please specify'
                ]
                return_reasons = "\n ".join([f"- {item}" for item in reasons])
                
                #output = f"Please select an order you want to initiate return for: \n\n {orders}"

                output = f"Please specify a product you want you want to initiate return for in the format 'OrderId, Product, Quantity, Return Reason': \n\n {orders} Return Reasons: \n {return_reasons}"
                
                return result
            except Exception as e:
                print(e)
        
        # @tool(return_direct=True)
        @tool
        def get_return_items(order_no: str) -> str:
            """Gets the list of products in order with order_no.
            Use it ONLY when the user asks for returning the products and gives the order number. For example `I would like to return products for order OT1002.`
            Return the output without processing further.
            """
            #result = self.db.getItemsByOrderId(order_no)
            result = [
                    {
                        "orderId": "OT1002",
                        "items": [
                            {
                                "name": "Graph Paper",
                                "price": "100",
                                "quantity": "2"
                            }
                        ]
                    },
                    {
                        "orderId": "OT1003",
                        "items": [
                            {
                                "name": "Blue Shirt",
                                "price": "300",
                                "quantity": "1"
                            }
                        ]
                    }
                ]

            #print(str(result))

            reasons = [
                'Low Quality',
                'Large Size',
                'Small Size',
                'Other - Please specify'
                ]
            return_reasons = "\n ".join([f"- {item}" for item in reasons])

            format = "\n ".join([f"- {item['name']}, Price: {item['price']},  Qty: {item['quantity']}" for item in result[0]['items']])
            orders = f"OrderId: {result[0]['orderId']} \n {format}"
            #output = f"Please select product you want to return: \n\n OrderId: {result[0]['orderId']} \n\n {format}"
            output = f"Please specify 'Product, Quantity: \n\n {orders} \n\n also mention Return Reason: \n {return_reasons}"
            return output
        
        @tool(return_direct=True)
        def get_return_reasons(product: str) -> str:
            """Gets the list of reasons for return.
            Use this to get list of return reasons once the user selects a product to return. 
            Return the output without processing further.
            """
            reasons = [
                'Low Quality',
                'Large Size',
                'Small Size',
                'Other - Please specify'
            ]
            format = "\n ".join([f"- {item}" for item in reasons])
            output = f"Added {product} for return. Please select reason for your return: \n\n {format}"
            return output
        
        @tool(return_direct=True)
        def get_email_for_return(reason: str) -> str:
            """Confirm email address.
            Use this to get email adress once the user selects a reason for return and only if user has not provided email address already. 
            Return the output without processing further.
            """
            
            output = f"Please provide email address for sending return label."
            return output
        
        #StructuredTool for multiple parameter values
        def generate_return_label(order_no:str, email: str, product: str, quantity:str, reason: str) -> str:
            """Generates return request label and sends it to email.
            Use this tool after user has selected product, quantity, return reason & gives email address for return. 
            Also ask user if you can assist with anything else'

            Return the output without processing further.
            """

            return_request = f""" Summary of return request: \n
            Order ID: {order_no}\n
            Product: {product}\n
            Quantity: {quantity}\n
            Return Reason: {reason}\n
            Email for return label: {email}
            """
            
            output = f"{return_request} \n\n Sent return label to given email address {email} for order {order_no}. Please return the items within 7 days. Refund will be completed within 30 days of receiving items. \n\n Can I assist you with anything else today?"
            return output
        
        label_tool = StructuredTool.from_function(generate_return_label)
        
        tools = [retrieve_products, add_product_to_cart,get_orders_for_return, get_return_items, get_email_for_return, label_tool]

        return tools
