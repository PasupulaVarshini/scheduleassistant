# Agentic RAG Schedule Assistant

An autonomous, Agentic RAG-powered schedule management system that manages a 30-day calendar using **ChromaDB vector database**, intelligent tool calling, and an interactive modern web interface.

---

## Features

- **Agentic Decision Engine**: Decides autonomously when to retrieve information and when to perform calendar mutations.
- **Two Core Tools**:
  1. `get_schedule`: Semantic vector search against ChromaDB, date & time filtering, and availability checking.
  2. `update_schedule`: Creates, updates, moves, or removes schedule entries with synchronized ChromaDB vector embeddings.
- **Preloaded 30-Day Calendar**: Populated with realistic meetings, workshops, tasks, and appointments across a 30-day timeline.
- **ChromaDB Vector Store**: Fast semantic search matching natural language intent (e.g., *"doctor checkup"*, *"Friday afternoon"*).
- **Execution Trace Inspector**: Live breakdown of the agent's thought process, tool selection, arguments, and vector retrieval context.
- **RESTful API & Interactive UI**: Built with FastAPI, Vanilla CSS, and modern JavaScript.

---

## Supported Query Examples

- *"What do I have scheduled tomorrow?"*
- *"Am I free Friday afternoon?"*
- *"Add a meeting on August 15 at 3 PM with Team Lead"*
- *"Move my meeting from 2 PM to 4 PM"*
- *"Show all workshops this month"*
- *"Cancel my dentist appointment"*

---

## Local Setup

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPO_URL>
   cd <REPO_FOLDER>
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   python main.py
   # or
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the application:**
   - Web Application: [http://localhost:8000](http://localhost:8000)
   - Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Deployment on Render

This project is fully configured for zero-setup deployment on [Render](https://render.com).

### Option A: Using Blueprint (Automatic)
1. Push this repository to GitHub.
2. In Render, click **New +** -> **Blueprint**.
3. Select your GitHub repository. Render reads `render.yaml` and sets up everything automatically.

### Option B: Manual Web Service
1. In Render, click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `agentic-rag-schedule-assistant`
   - **Language**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Click **Deploy Web Service**.
5. Once deployed, copy your Render URL (e.g. `https://your-service.onrender.com`) into `deployed_url.txt`.
