from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import LLMChain, PromptTemplate
from langchain.memory.buffer import ConversationBufferMemory
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain import PromptTemplate, LLMChain
import os

class CustomOutputParser(StrOutputParser):
    def parse(self, response: str):
        return response.split('[/INST]')[-1]


class StoryCreativityChain:

    INDEX_PATH = "faiss_index"  # folder or file name to save/load the index

    def __init__(self):
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            google_api_key="AIzaSyBuMm2PM4M5LxF3FX0lfiN9JiKT4eT8VQY",
            temperature=0.7,
            top_k=40,
            top_p=0.95,
            max_output_tokens=512
        )
       
       
        if os.path.exists(self.INDEX_PATH):
            print("Loading FAISS index from disk...")
            self.db = FAISS.load_local(self.INDEX_PATH, HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"), allow_dangerous_deserialization=True)
        else:
            print("Building new FAISS index...")
            self.db = self.build_faiss_index()
            self.db.save_local(self.INDEX_PATH)  # save index to disk for future use

        self.retriever = self.db.as_retriever()

    def getPromptFromTemplate(self):
        system_prompt = """You are a helpful assistant, you will use the provided history and context to answer user questions.
        Read the given context and history before answering questions and think step by step. If you cannot answer a user question based on
        the provided context, inform the user. Do not use any other information for answering the user. Provide a detailed answer to the question."""

        B_INST, E_INST = "[INST]", "[/INST]"
        B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
        SYSTEM_PROMPT1 = B_SYS + system_prompt + E_SYS

        instruction = """
        History: {history} \n
        Context: {context} \n
        User: {question}"""

        prompt_template = B_INST + SYSTEM_PROMPT1 + instruction + E_INST
        prompt = PromptTemplate(input_variables=["history", "question", "context"], template=prompt_template)

        return prompt

    def build_faiss_index(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "data.txt")

        loader = TextLoader(file_path)
        documents = loader.load()

        embeddings = HuggingFaceEmbeddings(model_name=model_name)

        from langchain.text_splitter import CharacterTextSplitter
        text_splitter = CharacterTextSplitter(chunk_size=10, chunk_overlap=0, separator=".")
        texts = text_splitter.split_documents(documents)

        db = FAISS.from_documents(texts, embeddings)
        return db

    def getNewChain(self):
        prompt = self.getPromptFromTemplate()
        memory = ConversationBufferMemory(input_key="question", memory_key="history", max_len=5)
        llm_chain = LLMChain(prompt=prompt, llm=self.llm, verbose=True, memory=memory,
                             output_parser=CustomOutputParser())
        rag_chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | llm_chain
        )
        return rag_chain


story_chain = StoryCreativityChain()
chain = story_chain.getNewChain()

class StoryCreativityView(APIView):
    def post(self, request):
        try:
            question = request.data.get("question", None)
            if not question:
                return Response({"error": "No question provided"}, status=status.HTTP_400_BAD_REQUEST)

            response = chain.invoke(question)

            return Response({"answer": response.get('text', '')}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)