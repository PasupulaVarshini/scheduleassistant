"""
FastAPI Server & Web Application for Agentic RAG Schedule Assistant.
Serves the REST API, Agent Chat Engine, ChromaDB Vector Pipeline, and Static Frontend.
"""
import os
from datetime import date
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from vector_store import ScheduleVectorStore
from agent import ScheduleAgent

app = FastAPI(
    title="Agentic RAG Schedule Assistant",
    description="Intelligent 30-Day Schedule Manager powered by ChromaDB Vector Search and Autonomous Agent Tools",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Vector Store and Agent
CURRENT_BASE_DATE = date(2026, 10, 13) # Aligned with system reference date
vector_store = ScheduleVectorStore(db_dir="./chroma_db", base_date=CURRENT_BASE_DATE)
agent = ScheduleAgent(vector_store=vector_store, base_date=CURRENT_BASE_DATE)


class ChatRequest(BaseModel):
    message: str
    reference_date: Optional[str] = None


class EventModel(BaseModel):
    id: Optional[str] = None
    title: str
    category: str = "meeting"
    date: str
    start_time: str
    end_time: str
    location: Optional[str] = "Online / Room"
    participants: Optional[List[str]] = []
    description: Optional[str] = ""
    status: Optional[str] = "confirmed"


class RAGSearchRequest(BaseModel):
    query: str
    n_results: Optional[int] = 5
    date_filter: Optional[str] = None
    category_filter: Optional[str] = None


# --- API Endpoints ---

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Processes user query through the Agentic RAG decision engine."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = agent.process_request(
        user_prompt=req.message,
        reference_date=req.reference_date
    )
    return result


@app.get("/api/schedule")
async def get_all_events():
    """Retrieves all scheduled events across the 30-day window."""
    events = vector_store.list_all_events()
    return {
        "count": len(events),
        "events": events
    }


@app.post("/api/events")
async def create_event(event: EventModel):
    """Directly creates a new schedule entry and updates ChromaDB."""
    created = vector_store.add_event(event.dict())
    return {"success": True, "event": created}


@app.put("/api/events/{event_id}")
async def update_event_by_id(event_id: str, event: EventModel):
    """Updates an existing schedule entry and re-indexes in ChromaDB."""
    payload = event.dict()
    payload["id"] = event_id
    updated = vector_store.update_event(payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "event": updated}


@app.delete("/api/events/{event_id}")
async def delete_event_by_id(event_id: str):
    """Deletes an event from database and vector index."""
    deleted = vector_store.delete_event(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"success": True, "message": "Event deleted successfully"}


@app.post("/api/reset")
async def reset_sample_data():
    """Resets schedule with pristine 30-day sample data."""
    vector_store.reset_sample_data(base_date=agent.base_date)
    return {"success": True, "message": "Schedule reset with 30 days of sample data", "total_events": len(vector_store.events_db)}


@app.post("/api/rag/search")
async def rag_direct_search(req: RAGSearchRequest):
    """Direct semantic vector search against ChromaDB."""
    matches = vector_store.query_rag(
        query_text=req.query,
        n_results=req.n_results or 5,
        date_filter=req.date_filter,
        category_filter=req.category_filter
    )
    return {"query": req.query, "results": matches}


@app.get("/api/stats")
async def get_system_stats():
    """Returns vector database status and category counts."""
    events = vector_store.list_all_events()
    counts = {"meeting": 0, "workshop": 0, "task": 0, "appointment": 0}
    for e in events:
        cat = e.get("category", "meeting").lower()
        if cat in counts:
            counts[cat] += 1

    return {
        "total_events": len(events),
        "vector_collection": "schedule_events",
        "chroma_count": vector_store.collection.count(),
        "categories": counts,
        "base_date": agent.base_date.strftime("%Y-%m-%d"),
        "date_range": {
            "start": events[0]["date"] if events else "",
            "end": events[-1]["date"] if events else ""
        }
    }


# Serve static files for frontend UI
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Agentic RAG Schedule Assistant API is online."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)

