"""
Sample Schedule Data Generator for Agentic RAG Schedule Assistant.
Generates 30 days of realistic meetings, workshops, tasks, and appointments.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any


def get_default_schedule(base_date: date = None) -> List[Dict[Any, Any]]:
    if base_date is None:
        base_date = date.today()

    # Pre-defined templates with relative day offsets and rich metadata
    templates = [
        # --- TODAY (Day 0) ---
        {
            "offset": 0,
            "title": "Daily Standup & Sprint Kickoff",
            "category": "meeting",
            "start_time": "09:30",
            "end_time": "10:00",
            "location": "Zoom Room Alpha",
            "participants": ["Alice", "Bob", "Charlie", "David"],
            "description": "Daily engineering standup discussing agentic RAG progress and blockers.",
            "status": "confirmed"
        },
        {
            "offset": 0,
            "title": "Deep Learning Workshop: Embeddings & Tokenizers",
            "category": "workshop",
            "start_time": "14:00",
            "end_time": "16:00",
            "location": "Main Auditorium & Online Stream",
            "participants": ["Dr. Henderson", "AI Research Team"],
            "description": "Interactive workshop exploring dense vector representations, similarity metrics, and embedding fine-tuning.",
            "status": "confirmed"
        },
        {
            "offset": 0,
            "title": "Review Pull Request #142 (Vector Store Indexer)",
            "category": "task",
            "start_time": "16:30",
            "end_time": "17:30",
            "location": "GitHub / Async",
            "participants": ["Self"],
            "description": "Perform comprehensive code review for ChromaDB vector indexing and metadata schema.",
            "status": "in-progress"
        },

        # --- TOMORROW (Day 1) ---
        {
            "offset": 1,
            "title": "Client Sprint Demo - Alpha Release",
            "category": "meeting",
            "start_time": "10:00",
            "end_time": "11:00",
            "location": "Conference Room B / Google Meet",
            "participants": ["Sarah Jenkins", "Client Execs", "Tech Leads"],
            "description": "Live demonstration of the Schedule Assistant Agent and vector search capabilities for stakeholders.",
            "status": "confirmed"
        },
        {
            "offset": 1,
            "title": "Product Strategy & Roadmap Sync",
            "category": "meeting",
            "start_time": "14:00",
            "end_time": "15:00",
            "location": "Executive Boardroom",
            "participants": ["VP of Engineering", "Head of Product", "Karthik"],
            "description": "Quarterly strategic review for AI tool integration, timeline planning, and milestones.",
            "status": "confirmed"
        },
        {
            "offset": 1,
            "title": "Dentist Checkup & Cleaning",
            "category": "appointment",
            "start_time": "17:00",
            "end_time": "18:00",
            "location": "Downtown Dental Clinic",
            "participants": ["Dr. Miller"],
            "description": "Routine dental examination and teeth cleaning appointment.",
            "status": "confirmed"
        },

        # --- DAY 2 ---
        {
            "offset": 2,
            "title": "1:1 with Engineering Lead",
            "category": "meeting",
            "start_time": "11:00",
            "end_time": "11:45",
            "location": "Private Office 3",
            "participants": ["Elena Rostova", "Self"],
            "description": "Bi-weekly career growth, feedback, and architectural delegation discussion.",
            "status": "confirmed"
        },
        {
            "offset": 2,
            "title": "Draft Q4 Infrastructure Cost Analysis",
            "category": "task",
            "start_time": "13:30",
            "end_time": "15:30",
            "location": "Workspace",
            "participants": ["Self"],
            "description": "Prepare detailed budget forecast comparing vector database cloud hosting vs on-prem.",
            "status": "pending"
        },

        # --- DAY 3 (FRIDAY if base is Tuesday 2026-10-13) ---
        {
            "offset": 3,
            "title": "Weekly All-Hands & Product Showcases",
            "category": "meeting",
            "start_time": "09:30",
            "end_time": "10:30",
            "location": "Virtual Town Hall",
            "participants": ["Entire Organization"],
            "description": "Company-wide weekly sync showcasing key accomplishments and announcing hackathon winners.",
            "status": "confirmed"
        },
        {
            "offset": 3,
            "title": "Focus Time: Agent Tool Chain Optimization",
            "category": "task",
            "start_time": "10:45",
            "end_time": "12:00",
            "location": "Quiet Pod 2",
            "participants": ["Self"],
            "description": "Deep work session profiling latency in RAG pipeline and tool execution dispatch.",
            "status": "pending"
        },
        # Friday afternoon is intentionally kept open for answering "Am I free Friday afternoon?"

        # --- DAY 4 (SATURDAY) ---
        {
            "offset": 4,
            "title": "Personal Trainer Fitness Session",
            "category": "appointment",
            "start_time": "09:00",
            "end_time": "10:15",
            "location": "Olympus Fitness Center",
            "participants": ["Trainer Mark"],
            "description": "Strength training, core stability exercises, and metabolic conditioning.",
            "status": "confirmed"
        },

        # --- DAY 5 (SUNDAY) ---
        {
            "offset": 5,
            "title": "Weekend Reading & Research: LangGraph Patterns",
            "category": "task",
            "start_time": "15:00",
            "end_time": "17:00",
            "location": "Home Library",
            "participants": ["Self"],
            "description": "Study multi-agent coordination architectures and memory persistence strategies.",
            "status": "pending"
        },

        # --- DAY 6 ---
        {
            "offset": 6,
            "title": "Architecture Review: Vector Store Sharding",
            "category": "meeting",
            "start_time": "10:00",
            "end_time": "11:30",
            "location": "Design Lab 1",
            "participants": ["Chief Architect", "Data Platform Team"],
            "description": "Evaluate multi-tenant isolation, HNSW indexing performance, and ChromaDB scaling.",
            "status": "confirmed"
        },
        {
            "offset": 6,
            "title": "Hands-on Agentic AI & RAG Workshop: Part 1",
            "category": "workshop",
            "start_time": "14:00",
            "end_time": "17:00",
            "location": "Tech Hub Innovation Room",
            "participants": ["Internal Engineers", "Instructor Alex"],
            "description": "Interactive workshop building autonomous agents equipped with tool calling and vector retrieval.",
            "status": "confirmed"
        },

        # --- DAY 7 ---
        {
            "offset": 7,
            "title": "Optometry Vision Exam",
            "category": "appointment",
            "start_time": "11:00",
            "end_time": "11:45",
            "location": "Apex Vision Care",
            "participants": ["Dr. Catherine Lin"],
            "description": "Annual eye exam, prescription renewal, and blue-light filter check.",
            "status": "confirmed"
        },
        {
            "offset": 7,
            "title": "Update OpenAPI Documentation & SDK Spec",
            "category": "task",
            "start_time": "14:00",
            "end_time": "16:00",
            "location": "Workspace",
            "participants": ["Self"],
            "description": "Document get_schedule and update_schedule tool endpoints with JSON schema schemas.",
            "status": "pending"
        },

        # --- DAY 8 ---
        {
            "offset": 8,
            "title": "Cross-Functional Sync with Marketing & Growth",
            "category": "meeting",
            "start_time": "13:00",
            "end_time": "14:00",
            "location": "Room 204",
            "participants": ["Growth Lead", "Product Marketing Specialist"],
            "description": "Discuss launch marketing campaigns and user onboarding guides for the assistant.",
            "status": "confirmed"
        },

        # --- DAY 9 ---
        {
            "offset": 9,
            "title": "Annual Comprehensive Health Checkup",
            "category": "appointment",
            "start_time": "08:30",
            "end_time": "10:30",
            "location": "St. Jude Wellness Center",
            "participants": ["Dr. Robert Evans"],
            "description": "Full blood panel, biometric measurements, ECG, and general health consultation.",
            "status": "confirmed"
        },
        {
            "offset": 9,
            "title": "Security & OWASP Top 10 Best Practices Workshop",
            "category": "workshop",
            "start_time": "14:00",
            "end_time": "16:30",
            "location": "Virtual Auditorium",
            "participants": ["SecOps Team", "Fullstack Developers"],
            "description": "Interactive cybersecurity workshop focusing on prompt injection defense and secure API auth.",
            "status": "confirmed"
        },

        # --- DAY 11 ---
        {
            "offset": 11,
            "title": "Benchmark ChromaDB vs Pinecone Latency",
            "category": "task",
            "start_time": "10:00",
            "end_time": "12:30",
            "location": "Cloud Benchmark Sandbox",
            "participants": ["Self"],
            "description": "Run p95 and p99 query latency benchmarks across 100,000 schedule vectors.",
            "status": "pending"
        },

        # --- DAY 12 ---
        {
            "offset": 12,
            "title": "Partnership Discussion with Cloudflare",
            "category": "meeting",
            "start_time": "15:00",
            "end_time": "16:00",
            "location": "Video Conference",
            "participants": ["Cloudflare Partner Manager", "Solutions Architect"],
            "description": "Evaluate Workers AI and Edge Vectorize integrations for sub-millisecond retrieval.",
            "status": "confirmed"
        },

        # --- DAY 14 ---
        {
            "offset": 14,
            "title": "Design System & UI Component Review",
            "category": "meeting",
            "start_time": "11:00",
            "end_time": "12:30",
            "location": "Creative Studio",
            "participants": ["Lead UI Designer", "Frontend Developers"],
            "description": "Review glassmorphic calendar design, color contrast tokens, and mobile touch targets.",
            "status": "confirmed"
        },
        {
            "offset": 14,
            "title": "Home High-Speed Fiber Internet Installation",
            "category": "appointment",
            "start_time": "14:00",
            "end_time": "16:00",
            "location": "Home Residence",
            "participants": ["Telecom Field Technician"],
            "description": "On-site installation and configuration of 2Gbps low-latency optical connection.",
            "status": "confirmed"
        },

        # --- DAY 16 ---
        {
            "offset": 16,
            "title": "Advanced Prompt Engineering & Guardrails Workshop",
            "category": "workshop",
            "start_time": "13:30",
            "end_time": "16:30",
            "location": "Learning Annex Room 10",
            "participants": ["Prompt Engineers", "Quality Analysts"],
            "description": "Hands-on session on few-shot formatting, chain-of-thought verification, and hallucination reduction.",
            "status": "confirmed"
        },

        # --- DAY 18 ---
        {
            "offset": 18,
            "title": "Q4 Budget Allocation & Resource Planning",
            "category": "meeting",
            "start_time": "10:00",
            "end_time": "11:30",
            "location": "Finance Suite 5",
            "participants": ["Director of Finance", "Engineering Managers"],
            "description": "Finalize cloud infrastructure budget, API tooling credits, and contractor allocations.",
            "status": "confirmed"
        },

        # --- DAY 20 ---
        {
            "offset": 20,
            "title": "Prepare Slide Deck for Executive Steering Committee",
            "category": "task",
            "start_time": "14:00",
            "end_time": "16:30",
            "location": "Workspace",
            "participants": ["Self"],
            "description": "Synthesize performance metrics, RAG accuracy graphs, and user satisfaction surveys.",
            "status": "pending"
        },

        # --- DAY 22 ---
        {
            "offset": 22,
            "title": "Microservices Resilience & Kubernetes Masterclass",
            "category": "workshop",
            "start_time": "10:00",
            "end_time": "13:00",
            "location": "Cloud Academy Online",
            "participants": ["Site Reliability Engineers", "Backend Architects"],
            "description": "Chaos engineering drills, pod auto-scaling, and distributed tracing walkthrough.",
            "status": "confirmed"
        },

        # --- DAY 24 ---
        {
            "offset": 24,
            "title": "Physiotherapy & Posture Ergonomics Session",
            "category": "appointment",
            "start_time": "16:00",
            "end_time": "17:00",
            "location": "Motion Physio Clinic",
            "participants": ["Dr. Sarah Gomez"],
            "description": "Desk posture alignment, cervical spine mobility exercises, and ergonomic recommendations.",
            "status": "confirmed"
        },

        # --- DAY 26 ---
        {
            "offset": 26,
            "title": "Sprint Retrospective & Continuous Improvement",
            "category": "meeting",
            "start_time": "15:00",
            "end_time": "16:30",
            "location": "Collab Lounge B",
            "participants": ["Scrum Master", "Product Pod Team"],
            "description": "Review sprint delivery speed, test automation coverage, and action items for next sprint.",
            "status": "confirmed"
        },

        # --- DAY 28 ---
        {
            "offset": 28,
            "title": "End-of-Month Dependency & Security Patching",
            "category": "task",
            "start_time": "11:00",
            "end_time": "13:00",
            "location": "Dev Environment",
            "participants": ["Self"],
            "description": "Upgrade NPM and Python pip dependencies, resolve Dependabot alerts, verify test suites.",
            "status": "pending"
        },

        # --- DAY 30 ---
        {
            "offset": 30,
            "title": "Monthly Strategic Milestone Celebration",
            "category": "meeting",
            "start_time": "17:00",
            "end_time": "18:30",
            "location": "Rooftop Garden Lounge",
            "participants": ["Entire Product & Tech Team"],
            "description": "Celebrate release milestones, recognize standout contributions, and social networking.",
            "status": "confirmed"
        }
    ]

    events = []
    for idx, t in enumerate(templates, start=1):
        event_date = base_date + timedelta(days=t["offset"])
        event_id = f"evt_{idx:03d}"
        events.append({
            "id": event_id,
            "title": t["title"],
            "category": t["category"],
            "date": event_date.strftime("%Y-%m-%d"),
            "day_of_week": event_date.strftime("%A"),
            "start_time": t["start_time"],
            "end_time": t["end_time"],
            "location": t["location"],
            "participants": t["participants"],
            "description": t["description"],
            "status": t["status"]
        })

    return events


if __name__ == "__main__":
    schedule = get_default_schedule()
    print(f"Generated {len(schedule)} sample events spanning 30 days.")
    for e in schedule[:5]:
        print(f"[{e['date']} {e['start_time']}-{e['end_time']}] ({e['category']}) {e['title']}")
