import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaLLM
from langchain_community.document_loaders import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Define paths
VECTORSTORE_PATH = "faiss_index_"

load_dotenv()

# get LLM model from environment variable
ollama_host = os.environ.get("OLLAMA_HOST")
ollama_llm_model = os.environ.get("OLLAMA_LLM_MODEL", "qwen2.5:7b")

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

print("Loading embedding model...")
# Auto device selection for embeddings
embedding_model_name = "sentence-transformers/all-mpnet-base-v2"
model_kwargs = {"device": "cuda:0"}  
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name, model_kwargs=model_kwargs)

# Check if FAISS vector store already exists
if os.path.exists(VECTORSTORE_PATH):
    print("Loading existing FAISS vector store...")
    vectorstore = FAISS.load_local(VECTORSTORE_PATH, embeddings, allow_dangerous_deserialization=True)
else:
    print("No existing vector store found. Creating a new one...")

    # Load the document
    loader = CSVLoader("medquad.csv", content_columns=["question", "answer"], encoding="utf-8")
    documents = loader.load()

    # Split the document into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30, separator="\n")
    docs = text_splitter.split_documents(documents=documents)

    # Create FAISS vector store
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    # Save FAISS store for future use
    vectorstore.save_local(VECTORSTORE_PATH)

print("Initializing retriever & LLM...")
# Create a retriever
retriever = vectorstore.as_retriever()

# Create the LLM with auto device selection
llm = OllamaLLM(model=ollama_llm_model, num_gpu=3, base_url=ollama_host)

# Create RetrievalQA
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)

@app.post("/query")
async def get_answer(request: QueryRequest):
    """API endpoint to handle user queries and return an answer."""
    try:
        response = qa.run(request.query)
        return {"query": request.query, "answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
