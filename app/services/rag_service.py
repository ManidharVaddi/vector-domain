from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from pathlib import Path
import uuid



# Initialize embeddings and LLM
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Global vector store
vector_store = None

def get_vector_store():
    global vector_store
    if vector_store is None:
        persist_directory = "chroma_db"
        Path(persist_directory).mkdir(exist_ok=True)
        vector_store = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
    return vector_store

def process_document(file_path: str, filename: str):
    #Process uploaded document and add to vector store
    try:
        # Load document
        if filename.lower().endswith('.pdf'):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")
        
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        
        # Add to vector store
        vector_store = get_vector_store()
        vector_store.add_documents(texts)
        
        return len(texts)
        
    except Exception as e:
        print(f"Error processing document: {e}")
        return 0
    


    
def ask_question(query: str):
    """Answer question using RAG"""
    vector_store = get_vector_store()
    
    llm = ChatGroq(
        model="llama-3.1-8b-instant",   # Updated to working model
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY")
    )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    
    result = qa_chain({"query": query})
    return {
        "answer": result["result"],
        "source_documents": len(result["source_documents"])
    }