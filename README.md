---
title: Odisha Disaster Management Assistant
emoji: 🌪️
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

#  Intelligent RAG-Driven Disaster Response and Information Agent for Odisha
## Multi-Agent • Multi-Modal RAG • Memory-Aware • Explainable AI System

An **AI-powered, multi-agent assistant** designed for **disaster-related information retrieval, weather intelligence, and historical analysis for Odisha**.  
The system combines **Retrieval-Augmented Generation (RAG)**, **agent-based orchestration**, **short-term conversational memory**, and **real-time tools** to deliver **accurate, source-grounded, and context-aware responses**.

---

#  Key Highlights

-  **True RAG (Retrieval-Augmented Generation)** with source citations
-  **Conversation Memory** (follow-up questions handled correctly)
-  **Multi-Agent Architecture** (Router + Specialized Agents)
-  **Live IMD Weather Data** via Selenium scraping
-  **Real-time Web Search** (Serper API)
-  **PDF Intelligence** (IMD bulletins & disaster reports)
-  **Evaluator Agent** for answer quality & confidence checks
-  **Full-Stack Ready** (FastAPI backend + Web UI frontend)

---

#  Problem Statement

Disaster-related queries (cyclones, weather alerts, historical impacts) often suffer from:

- Scattered data sources
- Hallucinated AI answers
- No source attribution
- Poor follow-up understanding

This project solves these challenges by building a **reliable, explainable, and memory-aware AI assistant** specifically focused on **Odisha disaster management knowledge**.

---

#  System Architecture (High Level)


## User Query Flow

User Query  
    ↓  
Memory Injection (Short-Term Context)  
    ↓  
Routing Policy (Intent Detection)  
    ↓  
┌──────────────┬──────────────┬──────────────┐
│ Calculator   │ Web Search   │ Weather Agent│
│ Tool         │ Tool         │ (IMD)        │
└──────────────┴──────────────┴──────────────┘

    ↓  

## Retrieval-Augmented Generation (RAG)

RAG Agent  
(ChromaDB + PDFs)  
    ↓  

## Evaluation Layer

Evaluator Agent  
(Quality & Confidence)  
    ↓  

## Final Output

Final Response  
(with Sources)

---

# 🤖 Agents & Their Responsibilities

## 1️⃣ Routing Agent (Primary Router)

- Decides which agent or tool should handle a query  
- Uses keyword + intent-based logic  

### Routes To:
- Calculator  
- Web Search  
- Weather  
- RAG  
- General LLM
  
---

## 2️⃣ RAG Agent (Core Intelligence)

- Uses **ChromaDB** vector store  
- Retrieves relevant chunks from:
  - Disaster reports (Cyclone Fani, Phailin, etc.)
  - Government PDFs  
- Generates grounded answers with source & page numbers  

### ✅ Example

> “(Source: Cyclone-Fani-2019-Odisha-DLNA-Report.pdf, Page: 178)”

---

---

## 🧩 Multi-Modal RAG (Planned & Extensible)

The system is designed to evolve from **text-only RAG** to **multi-modal Retrieval-Augmented Generation**, enabling richer disaster intelligence.

### Supported / Planned Modalities

- **Text**
  - Disaster reports
  - Government PDFs
  - IMD bulletins

- **Images (Planned)**
  - Cyclone path maps
  - Damage assessment images
  - Satellite imagery (pre/post disaster)

- **Geospatial Data (Planned)**
  - District-wise impact maps
  - Flood-prone zone overlays
  - Cyclone trajectory visualizations

---

### Multi-Modal RAG Workflow

1. User submits a query (text or future image/map input)
2. Router Agent detects modality type
3. Relevant retrievers are triggered:
   - Text → ChromaDB (PDF embeddings)
   - Images → Vision encoder (CLIP / ViT-based)
   - Maps → Metadata + geospatial embeddings
4. Retrieved multi-modal context is fused
5. LLM generates a grounded, explainable response

---

### Example (Future Capability)

**User Query:**  
“Show cyclone damage patterns in Puri during Fani”

**System Behavior:**
- Retrieves:
  - Textual reports (PDFs)
  - Damage maps
  - Satellite images
- Produces:
  - Text explanation
  - Visual references
  - Source attribution

---

### Why Multi-Modal RAG Matters

- Reduces hallucination in visual explanations
- Improves disaster situational awareness
- Enables decision support for authorities
- Aligns with real-world emergency response systems
  

---

## 3️⃣ Weather Agent (Live Data)

- Detects city/location from user query  
- Maps Odisha cities → IMD station IDs  
- Scrapes live IMD weather data using **Selenium**  
- Optionally reads IMD PDF bulletins  

---

## 4️⃣ Web Search Tool

- Uses **Serper API**  
- Handles:
  - Latest cyclone news  
  - Live updates  
  - Current alerts  

---

## 5️⃣ Evaluator Agent

- Checks response quality & confidence  
- Improves low-confidence answers using:
  - Web search  
  - RAG augmentation  
- Prevents hallucinations  

---

# 🧠 Memory Design

## 🔹 Short-Term Memory

- Stores last **N interactions** per session  
- Enables follow-up questions like:
  - “What was its speed?”
  - “How much damage did it cause?”  

### Implemented Using
- `ShortTermMemory()`

### Injected Before Routing, Ensuring
- Context continuity  
- Correct intent classification  
- Accurate retrieval  

---

## 🔹 Long-Term Memory (Extensible)

- Designed for:
  - User preferences  
  - Frequently asked facts  
  - Stored persistently on disk (**JSON**)  

---

# 🌐 Backend (FastAPI)

- Session-aware `/chat` endpoint  
- Each user gets a unique `session_id`  
- Memory preserved across requests  
- CORS enabled for frontend integration  

## Endpoint

### POST `/chat`

```json
{
  "query": "...",
  "session_id": "uuid"
}
```

---

# 🖥️ Frontend

- Clean chat interface (**HTML + CSS + JS**)  
- **IndexedDB** for chat history  
- Session ID stored in **localStorage**  
- Typing indicators & chat persistence  
- Works seamlessly with backend memory  

---

# 🛠️ Tech Stack

- Python  
- LangGraph  
- LangChain  
- ChromaDB  
- FastAPI  
- Groq LLMs  
- Selenium  
- Serper API  
- HTML / CSS / JavaScript  

---

🎯 Use Cases

Disaster impact analysis

Government & academic research

Emergency planning support

AI explainability demos

Interview-ready GenAI portfolio project

---

# 📈 Future Enhancements

- IMD official APIs (when available)  
- Multi-modal inputs (maps, images)  
- Alert classification & severity scoring  
- Persistent long-term memory with embeddings  
- Role-based responses (citizen vs authority)  

---

# 🙌 Author

**Subhakanta Rath**  
MSc AI & ML | Multi-Agent Systems | RAG | Applied AI  
📍 Odisha, India  

=======
---
title: Odisha Disaster Management Ai
emoji: ⚡
colorFrom: yellow
colorTo: purple
sdk: docker
pinned: false
license: mit
short_description: 'Multi-agent RAG-based AI assistant for Odisha disaster '
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> 824b6f1c3f5f0b56fbc2645076d26e5f966d610a
