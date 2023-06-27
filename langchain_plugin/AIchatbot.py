import os
import sys
import pickle
import traceback
import json
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains import ChatVectorDBChain

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

# read kimp_bot_config.json
file_name = 'kimp_bot_config.json'
json_full_dir = os.path.join(upper_dir, file_name)
with open(json_full_dir) as f:
    json_settings = json.loads(f.read())
    openai_api_key = json_settings['openai_api_key']

class ChatBot:
    def __init__(self, logging_dir, node):
        self.node = node
        self.chatbot_logger = KimpBotLogger("chatbot_logger", logging_dir).logger
        self.chatbot_logger.info(f"ChatBot logger is initialized.")
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vectordb = Chroma(persist_directory=f"{upper_dir}/langchain_plugin/chroma", embedding_function=self.embeddings)
        self.model = ChatOpenAI(temperature=0, model_name='gpt-3.5-turbo', openai_api_key=openai_api_key)
        # self.model = OpenAI(temperature=0.1, model_name='gpt-3.5-turbo', openai_api_key=openai_api_key)
        # self.model = ChatOpenAI(temperature=0, model_name='gpt-4', openai_api_key=openai_api_key)
        self.chain = ChatVectorDBChain.from_llm(self.model, self.vectordb, return_source_documents=True)

    def get_response(self, input_text, response_dict):
        try:
            response = self.chain({"question": input_text, "chat_history": []})
            response_dict['answer'] = response['answer']
            response_dict['finished'] = True
            # TEST
            self.chatbot_logger.info(f"GPT response: {response}")
            return response_dict
        except Exception as e:
            self.chatbot_logger.error(f"Error in get_response from gpt api: {traceback.format_exc()}")