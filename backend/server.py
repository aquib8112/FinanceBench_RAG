import asyncio
import json
import logging
from threading import Event, Thread

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
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

@app.post("/ask/stream")
async def ask_stream(payload: PromptPayload):
    events = asyncio.Queue()
    stopped = Event()
    loop = asyncio.get_running_loop()

    def emit(event):
        if not stopped.is_set():
            loop.call_soon_threadsafe(events.put_nowait, event)

    def notify(message):
        if stopped.is_set():
            raise InterruptedError("Client disconnected")
        emit({**(message if isinstance(message, dict) else {"message": message}), "type": "status"})

    def run():
        try:
            result = pipeline(payload.question, on_progress=notify)
            if result.get("error"):
                emit({"type": "error", "message": result["answer"]})
            else:
                emit({"type": "result", "data": {
                    key: result[key] for key in ("answer", "documents", "research") if key in result
                }})
        except InterruptedError:
            pass
        except Exception:
            logging.exception("Streaming research failed")
            emit({"type": "error", "message": "Research failed. Please try again."})

    async def stream():
        try:
            Thread(target=run, daemon=True).start()
            while True:
                try:
                    event = await asyncio.wait_for(events.get(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
                    continue
                yield "data: " + json.dumps(event, ensure_ascii=False) + "\n\n"
                if event["type"] in ("result", "error"):
                    return
        finally:
            stopped.set()

    return StreamingResponse(
        stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
