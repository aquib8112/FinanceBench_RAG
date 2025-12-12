from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from rag.search import pipeline

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptPayload(BaseModel):
    question: str

@app.post("/ask")
async def ask(payload: PromptPayload):
    question = payload.question

    response = pipeline(question)
    answer = response["answer"]
    selected_docs = response["documents"]

    return {
        "answer": answer,
        "documents": selected_docs
    }