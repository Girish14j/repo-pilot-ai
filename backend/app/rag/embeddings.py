import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.rag.knowledge_base import KNOWLEDGE_BASE

load_dotenv()

# Path where Chroma stores its data on disk
# This means the vector DB persists between restarts
CHROMA_PERSIST_PATH = "./chroma_db"


def build_vector_store() -> Chroma:
    """
    Converts our knowledge base into a searchable vector store.
    
    Steps:
    1. Convert raw knowledge base entries into LangChain Documents
    2. Split long documents into smaller chunks
    3. Embed each chunk using OpenAI embeddings
    4. Store embeddings in Chroma vector database
    
    This runs once at startup. Subsequent calls load from disk.
    """

    # OpenAI's text-embedding-3-small is cheap, fast, and high quality
    # We use OpenRouter here too for consistency
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1/",
    )

    # If the vector store already exists on disk, load it
    # This avoids re-embedding every time the server starts
    if os.path.exists(CHROMA_PERSIST_PATH):
        print("📚 RAG: Loading existing vector store from disk...")
        return Chroma(
            persist_directory=CHROMA_PERSIST_PATH,
            embedding_function=embeddings,
        )

    print("📚 RAG: Building vector store from knowledge base...")

    # Step 1: Convert knowledge base entries to LangChain Document objects
    # Document is LangChain's standard wrapper: content + metadata
    documents = [
        Document(
            page_content=entry["content"],
            metadata=entry["metadata"]
        )
        for entry in KNOWLEDGE_BASE
    ]

    # Step 2: Split documents into chunks
    # RecursiveCharacterTextSplitter splits on paragraphs first,
    # then sentences, then words — always trying to keep semantic units together
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,       # max characters per chunk
        chunk_overlap=50,     # overlap between chunks to preserve context
        separators=["\n\n", "\n", ". ", " "],  # split order preference
    )
    chunks = splitter.split_documents(documents)

    print(f"📚 RAG: Created {len(chunks)} chunks from {len(documents)} documents")

    # Step 3 + 4: Embed chunks and store in Chroma
    # from_documents() handles both embedding and storage in one call
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PERSIST_PATH,
    )

    print("✅ RAG: Vector store built and saved to disk")
    return vector_store


# Build once at module load — reused by all agents
vector_store = build_vector_store()