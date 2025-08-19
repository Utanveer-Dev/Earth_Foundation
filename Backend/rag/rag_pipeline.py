import os
from langchain_google_genai import ChatGoogleGenerativeAI

# Using new imports from LangChain v0.2+ and langchain_community for embeddings, loaders, vectorstores
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables import RunnableLambda
from typing import Annotated
from langchain_core.runnables import Runnable

from role_states.adult_states import ADULT_FLOW

from google import genai


class CustomOutputParser(StrOutputParser):
    def parse(self, response: str):
        return response.split('[/INST]')[-1]


class HistoryToStringRunnable(Runnable):
    def invoke(self, history_obj):
        if hasattr(history_obj, "messages"):
            return "\n".join(msg.content for msg in history_obj.messages)
        return ""
    

store = {}

def get_session_history(user_id: str) -> BaseChatMessageHistory:
    """Retrieve or create chat history for a given user + conversation."""
    
    print("user_id:", user_id)
    
    if (user_id) not in store:
        store[(user_id)] = ChatMessageHistory()
    return store[(user_id)]


class StoryCreativityChain:

    INDEX_PATH = "faiss_index"  # folder or file name to save/load the index

    def __init__(self):
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            google_api_key="AIzaSyANj4bwTAp1cCRf6m5xiZGlVfxZtZx365Q",
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=512
        )
       
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Go up one level to the parent folder
        parent_dir = os.path.dirname(current_dir)

        # Path to faiss_index folder
        faiss_path = os.path.join(parent_dir, "faiss_index")
       
        print("FAISS index path from disk...", faiss_path)
        if os.path.exists(faiss_path):
            print("Loading FAISS index from disk...")
            self.db = FAISS.load_local(faiss_path, HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"), allow_dangerous_deserialization=True)
        else:
            print("FAISS index not present")
            # self.db = self.build_faiss_index()
            # self.db.save_local(faiss_path)  # saving index to disk for future use

        self.retriever = self.db.as_retriever()


    def get_retriever(self):
        return self.retriever


    def get_flow_step(self, index: int, ADULT_FLOW_LIST):
        """Return the prompt and system instruction for a given index."""
        if 0 <= index < len(ADULT_FLOW_LIST):
            step = ADULT_FLOW_LIST[index]
            return step["system_instruction"], step["prompt"]
        else:
            raise IndexError("Invalid step index")


    def getPromptFromTemplate(self, index):
        
        # Convert to indexed list
        ADULT_FLOW_LIST = list(ADULT_FLOW.values())

        system_instruction, prompt = self.get_flow_step(index, ADULT_FLOW_LIST)
        
        # system_prompt = "Instruction: " + instruction + "\n" + prompt
        
        B_INST, E_INST = "[INST]", "[/INST]"
        B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
        SYSTEM_PROMPT1 = B_SYS + system_instruction + '\n' + prompt + E_SYS

        instruction = """
        History: {history} \n
        Context: {context} \n
        User: {question}"""

        prompt_template = B_INST + SYSTEM_PROMPT1 + instruction + E_INST
        
        # prompt_template = system_prompt + instruction
        
        prompt = PromptTemplate(input_variables=["history", "question", "context"], template=prompt_template)

        return prompt


    # def build_faiss_index(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    #     current_dir = os.path.dirname(os.path.abspath(__file__))
    #     file_path = os.path.join(current_dir, "data.txt")

    #     print("file path:", file_path)

    #     loader = TextLoader(file_path)
    #     documents = loader.load()

    #     embeddings = HuggingFaceEmbeddings(model_name=model_name)

    #     # from langchain.text_splitter import CharacterTextSplitter
    #     text_splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=0, separator=".")
    #     texts = text_splitter.split_documents(documents)

    #     db = FAISS.from_documents(texts, embeddings)
    #     return db

    def getNewChain(self):
        prompt = self.getPromptFromTemplate(0)
        memory = ConversationBufferMemory(input_key="question", memory_key="history", max_len=5)
        llm_chain = LLMChain(prompt=prompt, llm=self.llm, verbose=True, memory=memory,
                             output_parser=CustomOutputParser())
        
        rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | llm_chain
        )
        
        # rag_chain_with_history = RunnableWithMessageHistory(
        #     rag_chain,
        #     get_session_history,
        #     input_messages_key="question",
        #     history_messages_key="history",
        #     configurable_fields=[
        #             ConfigurableFieldSpec(id="session_id", annotation=str, name="Session ID", description="Unique user id")
        #         ]
        #     )
        
        return rag_chain, llm_chain


    def create_gating_chain(self):
        gating_prompt = PromptTemplate(
            input_variables=["input"],
            template="""
Decide whether the following user query requires retrieving external documents to answer it. Retrieving external documents is required if user asks anything (e.g information, etc.).
Return only "YES" if user asks anything and "NO" if it's a simple greeting.

Query:
{input}
""")
        
        return LLMChain(prompt=gating_prompt, llm=self.llm, output_parser=StrOutputParser())


    def create_reformulation_chain(self):
        reformulate_prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""
Given the conversation history and a follow-up question, rephrase the question to be a standalone question.

History:
{history}

Follow-up question:
{input}

Standalone question:
"""
        )
        return LLMChain(prompt=reformulate_prompt, llm=self.llm, output_parser=StrOutputParser())