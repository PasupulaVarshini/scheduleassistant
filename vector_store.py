"""
Vector Database & RAG Pipeline for Schedule Assistant using ChromaDB.
Manages persistent vector collection, document formatting, semantic retrieval, and CRUD operations.
"""
import os
import json
import math
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from sample_data import get_default_schedule


class FastSemanticEmbeddingFunction(EmbeddingFunction):
    """
    High-performance semantic embedding function generating normalized 384-dimensional
    dense vectors using subword token n-grams and semantic feature hashing.
    Runs 100% locally with zero external network latency or HuggingFace token requirements.
    """
    def __init__(self, dim: int = 384):
        self.dim = dim

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            embeddings.append(self._embed_text(text))
        return embeddings

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        clean_text = text.lower()
        words = re.findall(r"\b\w+\b", clean_text)

        # Weight key temporal and categorical indicators higher
        high_importance_keywords = {
            "meeting": 2.5, "sync": 2.2, "demo": 2.0, "workshop": 2.8,
            "task": 2.2, "review": 2.0, "appointment": 2.8, "checkup": 2.5,
            "dentist": 3.0, "doctor": 3.0, "exam": 2.5, "standup": 2.2,
            "tomorrow": 2.0, "today": 2.0, "friday": 2.5, "morning": 2.0,
            "afternoon": 2.0, "evening": 2.0, "am": 1.8, "pm": 1.8
        }

        # Word level embeddings
        for w in words:
            weight = high_importance_keywords.get(w, 1.0)
            h = hash(w) % self.dim
            vec[h] += weight * 1.5

            # 3-gram character shingles for subword semantic fuzziness
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    shingle = w[i:i+3]
                    sh = hash(shingle) % self.dim
                    vec[sh] += 0.35 * weight

        # Bigram shingles
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            bh = hash(bigram) % self.dim
            vec[bh] += 1.2

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        else:
            vec[0] = 1.0
        return vec


class ScheduleVectorStore:
    def __init__(self, db_dir: str = "./chroma_db", base_date: date = None):
        self.db_dir = db_dir
        self.base_date = base_date or date.today()
        os.makedirs(db_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(path=self.db_dir)
        self.embedding_fn = FastSemanticEmbeddingFunction(dim=384)
        
        self.collection = self.client.get_or_create_collection(
            name="schedule_events",
            embedding_function=self.embedding_fn,
            metadata={"description": "User schedule events and temporal metadata"}
        )

        # In-memory dictionary for rapid lookup and serialization
        self.events_db: Dict[str, Dict[str, Any]] = {}
        self._load_or_initialize()

    def _format_event_doc(self, event: Dict[str, Any]) -> str:
        participants_str = (
            ", ".join(event["participants"])
            if isinstance(event.get("participants"), list)
            else str(event.get("participants", ""))
        )
        return (
            f"Event Title: {event.get('title', '')}\n"
            f"Category: {event.get('category', '')}\n"
            f"Date: {event.get('date', '')} ({event.get('day_of_week', '')})\n"
            f"Time Window: {event.get('start_time', '')} to {event.get('end_time', '')}\n"
            f"Location / Channel: {event.get('location', '')}\n"
            f"Participants: {participants_str}\n"
            f"Status: {event.get('status', 'confirmed')}\n"
            f"Description: {event.get('description', '')}"
        ).strip()

    def _load_or_initialize(self):
        existing_count = self.collection.count()
        data_json_path = os.path.join(self.db_dir, "events_backup.json")

        if existing_count > 0 and os.path.exists(data_json_path):
            try:
                with open(data_json_path, "r", encoding="utf-8") as f:
                    self.events_db = json.load(f)
                return
            except Exception:
                pass

        # Populate with fresh sample 30-day schedule
        self.reset_sample_data(self.base_date)

    def _persist_events_backup(self):
        data_json_path = os.path.join(self.db_dir, "events_backup.json")
        try:
            with open(data_json_path, "w", encoding="utf-8") as f:
                json.dump(self.events_db, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save events backup: {e}")

    def reset_sample_data(self, base_date: date = None):
        if base_date is not None:
            self.base_date = base_date

        # Clear existing collection
        try:
            self.client.delete_collection("schedule_events")
        except Exception:
            pass

        self.collection = self.client.create_collection(
            name="schedule_events",
            embedding_function=self.embedding_fn,
            metadata={"description": "User schedule events and temporal metadata"}
        )

        samples = get_default_schedule(self.base_date)
        self.events_db = {e["id"]: e for e in samples}

        docs = []
        ids = []
        metadatas = []

        for e in samples:
            doc = self._format_event_doc(e)
            docs.append(doc)
            ids.append(e["id"])
            metadatas.append({
                "id": e["id"],
                "title": e["title"],
                "category": e["category"],
                "date": e["date"],
                "start_time": e["start_time"],
                "end_time": e["end_time"],
                "location": e.get("location", ""),
                "status": e.get("status", "confirmed")
            })

        self.collection.add(
            documents=docs,
            ids=ids,
            metadatas=metadatas
        )
        self._persist_events_backup()

    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self.events_db.get(event_id)

    def list_all_events(self) -> List[Dict[str, Any]]:
        # Sort chronologically by date then start_time
        return sorted(
            list(self.events_db.values()),
            key=lambda x: (x.get("date", ""), x.get("start_time", ""))
        )

    def add_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        # Assign ID if not provided
        if "id" not in event_data or not event_data["id"]:
            existing_indices = [
                int(k.replace("evt_", ""))
                for k in self.events_db.keys()
                if k.startswith("evt_") and k.replace("evt_", "").isdigit()
            ]
            next_idx = max(existing_indices, default=0) + 1
            event_data["id"] = f"evt_{next_idx:03d}"

        # Ensure day_of_week is set
        if "date" in event_data and ("day_of_week" not in event_data or not event_data["day_of_week"]):
            try:
                d = datetime.strptime(event_data["date"], "%Y-%m-%d")
                event_data["day_of_week"] = d.strftime("%A")
            except Exception:
                event_data["day_of_week"] = ""

        # Normalize fields
        event_data.setdefault("status", "confirmed")
        event_data.setdefault("location", "TBD")
        event_data.setdefault("participants", [])
        event_data.setdefault("description", event_data.get("title", ""))

        self.events_db[event_data["id"]] = event_data

        doc = self._format_event_doc(event_data)
        metadata = {
            "id": event_data["id"],
            "title": event_data.get("title", ""),
            "category": event_data.get("category", "meeting"),
            "date": event_data.get("date", ""),
            "start_time": event_data.get("start_time", "09:00"),
            "end_time": event_data.get("end_time", "10:00"),
            "location": event_data.get("location", ""),
            "status": event_data.get("status", "confirmed")
        }

        self.collection.upsert(
            documents=[doc],
            ids=[event_data["id"]],
            metadatas=[metadata]
        )
        self._persist_events_backup()
        return event_data

    def update_event(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        event_id = event_data.get("id")
        if not event_id or event_id not in self.events_db:
            return None

        # Merge updates
        existing = self.events_db[event_id]
        existing.update({k: v for k, v in event_data.items() if v is not None})

        # Update day of week if date changed
        if "date" in event_data:
            try:
                d = datetime.strptime(existing["date"], "%Y-%m-%d")
                existing["day_of_week"] = d.strftime("%A")
            except Exception:
                pass

        doc = self._format_event_doc(existing)
        metadata = {
            "id": existing["id"],
            "title": existing.get("title", ""),
            "category": existing.get("category", "meeting"),
            "date": existing.get("date", ""),
            "start_time": existing.get("start_time", "09:00"),
            "end_time": existing.get("end_time", "10:00"),
            "location": existing.get("location", ""),
            "status": existing.get("status", "confirmed")
        }

        self.collection.update(
            documents=[doc],
            ids=[existing["id"]],
            metadatas=[metadata]
        )
        self._persist_events_backup()
        return existing

    def delete_event(self, event_id: str) -> bool:
        if event_id not in self.events_db:
            return False

        del self.events_db[event_id]
        try:
            self.collection.delete(ids=[event_id])
        except Exception as e:
            print(f"ChromaDB delete error: {e}")

        self._persist_events_backup()
        return True

    def query_rag(
        self,
        query_text: str,
        n_results: int = 5,
        date_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves matching schedule entries via semantic vector search in ChromaDB.
        Combines vector similarity with optional metadata filtering.
        """
        where_clause = None
        conditions = []
        if date_filter:
            conditions.append({"date": {"$eq": date_filter}})
        if category_filter:
            conditions.append({"category": {"$eq": category_filter}})

        if len(conditions) == 1:
            where_clause = conditions[0]
        elif len(conditions) > 1:
            where_clause = {"$and": conditions}

        total_items = self.collection.count()
        if total_items == 0:
            return []

        limit = min(n_results, total_items)
        try:
            res = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=where_clause
            )
        except Exception:
            # If where clause was too restrictive or syntax error, fallback without where
            res = self.collection.query(
                query_texts=[query_text],
                n_results=limit
            )

        retrieved_events = []
        if res and "ids" in res and res["ids"] and len(res["ids"][0]) > 0:
            matched_ids = res["ids"][0]
            distances = res.get("distances", [[]])[0] if "distances" in res else []
            documents = res.get("documents", [[]])[0] if "documents" in res else []

            for idx, m_id in enumerate(matched_ids):
                full_event = self.events_db.get(m_id)
                if full_event:
                    distance = distances[idx] if idx < len(distances) else 0.0
                    doc_snippet = documents[idx] if idx < len(documents) else ""
                    # Similarity score (1 / (1 + distance))
                    similarity = round(1.0 / (1.0 + distance), 3)
                    item = dict(full_event)
                    item["_similarity"] = similarity
                    item["_doc_snippet"] = doc_snippet
                    retrieved_events.append(item)

        # Sort by similarity desc
        retrieved_events.sort(key=lambda x: x.get("_similarity", 0), reverse=True)
        return retrieved_events
