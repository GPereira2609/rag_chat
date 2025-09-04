import os  
import psycopg

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
from langchain_postgres.vectorstores import PGVector
from config import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
)

def database_init(connection: str) -> None:
    with connection.cursor() as conn:
        sql = f"""
        CREATE TABLE IF NOT EXISTS processed_files (
            id SERIAL PRIMARY KEY,
            filename TEXT UNIQUE NOT NULL,
            processed_at timestamp DEFAULT NOW()
        );
        """

        conn.execute(sql)
    connection.commit()

def create_rag_chain(pdf_files: list[str]) -> RetrievalQA:
    
    CONNECTION_STRING = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    COLLECTION_NAME = "documentos_projeto"
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    connection = psycopg.connect(CONNECTION_STRING)
    database_init(connection) 

    vectorstore = PGVector(
        connection=CONNECTION_STRING,
        collection_name=COLLECTION_NAME,
        embeddings=embeddings,
    )

    processed_filenames = set()
    with connection.cursor() as cur:
        cur.execute("SELECT filename FROM processed_files;")
        for record in cur:
            processed_filenames.add(record[0])
    print(f"INFO: Encontrados {len(processed_filenames)} arquivos já processados no banco de dados.")

    files_to_process = []
    for f_path in pdf_files:
        filename = os.path.basename(f_path)
        if filename not in processed_filenames:
            files_to_process.append(f_path)
        else:
            print(f"INFO: Arquivo '{filename}' já processado. Pulando.")

    if files_to_process:
        print(f"INFO: Processando {len(files_to_process)} novos arquivos...")
        all_documents = []
        for pdf_file in files_to_process:
            if not os.path.exists(pdf_file):
                print(f"AVISO: Arquivo não encontrado em {pdf_file}")
                continue
            loader = PyPDFLoader(pdf_file)
            documents = loader.load()
            all_documents.extend(documents)

        if all_documents:
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(all_documents)
            
            vectorstore.add_documents(splits)
            print("INFO: Novos documentos adicionados ao Vector Store com sucesso.")

            with connection.cursor() as cur:
                for f_path in files_to_process:
                    filename = os.path.basename(f_path)
                    cur.execute("INSERT INTO processed_files (filename) VALUES (%s) ON CONFLICT (filename) DO NOTHING;", (filename,))
            connection.commit()
            print("INFO: Nomes dos novos arquivos registrados na tabela de controle.")
    else:
        print("INFO: Nenhum arquivo novo para processar. O agente está pronto para consulta.")

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")
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

