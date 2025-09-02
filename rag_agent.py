import tempfile
import os  

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

def create_rag_chain(pdf_files: list[str]) -> RetrievalQA:
    """
    Cria a cadeia de RAG a partir de uma lista de arquivos PDF locais.
    """
    load_dotenv()
    
    # Lista para armazenar todos os documentos carregados
    all_documents = []

    # 1. Carrega cada documento da lista de arquivos
    for pdf_file in pdf_files:
        if not os.path.exists(pdf_file):
            raise FileNotFoundError(f"O arquivo não foi encontrado no caminho: {pdf_file}")
        
        loader = PyPDFLoader(pdf_file)
        documents = loader.load()
        all_documents.extend(documents)

    # 2. Divide os documentos em pedaços (chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(all_documents)

    # 3. Cria os embeddings e o Vector Store (ChromaDB)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)

    # 4. Inicializa o modelo Gemini e a cadeia de RAG
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, 
        retriever=vectorstore.as_retriever()
    )
    return qa_chain

def start_rag_agent():
    files = [
    f"upload/{file}" for file in os.listdir("upload")
    ]

    return create_rag_chain(files)

