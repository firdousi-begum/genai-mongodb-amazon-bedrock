import boto3
from langchain.chains import ConversationChain, ConversationalRetrievalChain, RetrievalQA
from langchain.llms.bedrock import Bedrock
from langchain.chat_models.bedrock import BedrockChat
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import AgentType, initialize_agent
from langchain.schema import BaseMessage
from langchain.prompts.chat import MessagesPlaceholder
import langchain

class LangChainAssistant():
    # We are also providing a different chat history retriever which outputs the history as a Claude chat (ie including the \n\n)
    _ROLE_MAP = {"human": "\n\nHuman: ", "ai": "\n\nAssistant: "}

    def __init__(self, modelId,bedrock_client, model_args = {"temperature": 0.7, "max_tokens_to_sample": 2048},
                model_type="chat_doc", retriever = None, chat_memory= None, prompt_data = None,
                tools=None, logger=None):
        self.bedrock_a= bedrock_client
        self.retriever = retriever
        self.model_type = model_type
        if model_type == "chat_doc":
            self.llm, self.model, self.memory  = self.load_chat_doc_model(modelId, model_args, prompt_data, chat_memory)
        elif model_type == "chat_agent":
            self.llm, self.model, self.memory  = self.load_agent_model(modelId, model_args,prompt_data, tools, chat_memory)
        elif model_type == "chat_qa":
            self.llm, self.model  = self.load_qa_model(modelId, model_args,prompt_data)

        self.logger = logger
    
    def run(self, input_text):
        if hasattr(self, 'memory'):
            print(self.memory.buffer)

        if self.model_type == "chat_doc":
            result= self.chat_doc(input_text)
        elif self.model_type == "chat_agent":
            result = self.chat_agent(input_text)
        return result


    def load_chat_model(self, modelId, model_args, chat_memory):

        #print('In chat')
        # Setup bedrock
        llm = Bedrock(
            model_id= modelId,
            client= self.bedrock_a,
        )
        llm.model_kwargs = model_args

        if 'anthropic' in modelId:
            memory = ConversationBufferMemory(human_prefix="Human", ai_prefix="Assistant",)
            model = ConversationChain(llm=llm, verbose=True, memory= memory)
            model.prompt = self._get_claude_prompt()
        else:
            memory=ConversationBufferMemory()
            model = ConversationChain(llm=llm, verbose=True, memory=memory)
        return llm, model, memory
    
    def chat(self, input_text):
        #num_tokens = self.llm.get_num_tokens(input_text)
        num_tokens = 0 #Commenting for performance
        response = self.model.predict(input=input_text)
        return response, num_tokens
    
    def load_qa_model(self, modelId, model_args, prompt_data):

        #print('In chat doc')
        # Setup bedrock
        llm = BedrockChat(
            model_id= modelId,
            client= self.bedrock_a,
        )
        llm.model_kwargs = model_args

        Product_PROMPT = PromptTemplate(
            template=prompt_data, input_variables=["context", "question"]
        )

        model = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=self.retriever,
        verbose = True,
        #return_source_documents=True,
        chain_type_kwargs={"prompt": Product_PROMPT}
        )
        
        return llm, model

    def load_chat_doc_model(self, modelId, model_args, prompt_data, chat_memory):
        #print('In chat doc')
        # Setup bedrock
        llm = Bedrock(
            model_id= modelId,
            client= self.bedrock_a,
        )
        llm.model_kwargs = model_args

        if 'anthropic' in modelId:
            condense_prompt = self._create_prompt_template_claude()
            prompt_template = f"Human:{prompt_data}\n\nAssistant:"
        else:
            condense_prompt = self._create_prompt_template()
            prompt_template = f"{prompt_data}"

        memory = self._load_chat_memory(chat_memory)
        model = ConversationalRetrievalChain.from_llm(
            llm=llm, 
            retriever =self.retriever,
            memory=memory,
            verbose=True,
            condense_question_prompt= condense_prompt, 
            chain_type='stuff', # 'refine',
            return_source_documents=True,
            get_chat_history=self._get_chat_history,
            max_tokens_limit=4096
        )

        model.combine_docs_chain.llm_chain.prompt = PromptTemplate.from_template(prompt_template)
        
        return llm, model, memory
    
    def chat_doc(self, input_text, callbacks=[]):
        response = self.model(input_text)
        return response['answer']
    
    def load_agent_model(self, modelId, model_args, prefix, tools, chat_memory):
        #print('In chat doc')
        # Setup bedrock
        
        llm = BedrockChat(
            model_id= modelId,
            client= self.bedrock_a,
        )
        llm.model_kwargs = model_args

        PREFIX = prefix

        SUFFIX = """
        Previous conversation history:
        <history>{chat_history}</history>
        """
        langchain.debug=True

        memory = ConversationBufferMemory(
            k= 3,
            ai_prefix="Assistant",
            memory_key="chat_history",
            return_messages=True
        )
        memory.chat_memory.add_ai_message(f"How can I help you?")

        chat_history = MessagesPlaceholder(variable_name="chat_history")

        #memory = self._load_chat_memory(chat_memory)
        model = initialize_agent(
            tools,
            llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=2,
            agent_kwargs={
                "prefix": PREFIX,
                'suffix' : SUFFIX,
                "memory_prompts": [chat_history],
                "input_variables": ["input", "agent_scratchpad", "chat_history"]
            },
            memory=memory,
            #prompt= ANTHROPIC_PROMPT,
        )

        #print(model.agent.llm_chain.prompt.template)
        
        return llm, model, memory
    
    
    def chat_agent(self, input_text, callbacks=[]):
        response = self.model.run(input_text)
        return response
    
    def clear_history(self, initial_text=None):
        self.model.memory.clear()
        if initial_text is not None:
            self.model.memory.chat_memory.add_ai_message(initial_text)
        #self.logger.info("History cleared")
        return True
    
    def _load_chat_memory(self, chat_memory):
        if chat_memory is not None:
            memory = ConversationBufferMemory(ai_prefix="Assistant", k=3, memory_key="chat_history", chat_memory=chat_memory, output_key="answer", return_messages=True)
        else:
            memory = ConversationBufferMemory(memory_key="chat_history", k=3, ai_prefix="Assistant", output_key="answer", return_messages=True)

        return memory


    def _get_claude_prompt(self):
        prompt = PromptTemplate.from_template("""
        System: The following is a friendly conversation between a human and an AI.
        The AI is talkative and provides lots of specific details from its context. If the AI does not know
        the answer to a question, it truthfully says it does not know.

        Current conversation:
        <conversation_history>
        {history}
        </conversation_history>

        Here is the human's next reply:
        Human: {input}

        Assistant:
        """)
        return prompt
    
    def _create_prompt_template(self):
        _template = """{chat_history}

        Answer only with the new question.
        How would you ask the question considering the previous conversation: {question}
        Question:"""
        
        CONVO_QUESTION_PROMPT = PromptTemplate.from_template(_template)
        return CONVO_QUESTION_PROMPT
    
    def _create_prompt_template_claude(self):
        prompt_data ="""
            <conversation>{chat_history}</conversation>

            Human: How would you ask the question considering the previous conversation above? Only include new question in the ouput without xml tags. 
            <question>{question}</question>"""
        
        prompt_template = f"{prompt_data}\n\nAssistant:"
        condense_prompt_claude = PromptTemplate.from_template(prompt_template)
        
        return condense_prompt_claude
    
    def _get_chat_history(self,chat_history):
        buffer = ''
        for dialogue_turn in chat_history:
            #print(f"Type: {dialogue_turn.type}")
            if isinstance(dialogue_turn, BaseMessage):
                role_prefix = self._ROLE_MAP.get(dialogue_turn.type, f"{dialogue_turn.type}: ")
                buffer += f"\n{role_prefix}{dialogue_turn.content}"
            elif isinstance(dialogue_turn, tuple):
                human = "\n\nHuman: " + dialogue_turn[0]
                ai = "\n\nAssistant: " + dialogue_turn[1]
                buffer += "\n" + "\n".join([human, ai])
            else:
                raise ValueError(
                    f"Unsupported chat history format: {type(dialogue_turn)}."
                    f" Full chat history: {chat_history} "
                )
        return buffer