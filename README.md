

# Gemini RAG Chatbot: Neo4j + LangChain + Google Gemini

This project is an **end-to-end Retrieval-Augmented Generation (RAG) chatbot** that combines:

-   **Google Gemini** for natural language understanding, Cypher query generation, and answer synthesis
    
-   **Neo4j AuraDB** as a graph database and vector index for structured hospital data and unstructured patient reviews
    
-   **LangChain** for chain orchestration, prompt engineering, retrieval pipelines, and tool-enabled agents
    
-   **FastAPI** backend and **Streamlit** frontend UI for interaction
    
-   **Docker Compose** for containerized deployment
    

The project demonstrates how **knowledge graphs** and **semantic search** can be unified into a single conversational agent that can reason over structured hospital data **and** patient reviews.

----------

## 📌 Core Idea

Most chatbots rely only on vector-based semantic search, which works well for documents but struggles with **structured queries** (e.g., _"Which hospital has the most visits in 2023?"_).

This chatbot integrates **two complementary approaches**:

1.  **Cypher-based QA** — Converts natural language into **Cypher queries** for structured graph reasoning (counts, averages, relationships).
    
2.  **Vector-based QA** — Retrieves **patient reviews** semantically using embeddings stored in Neo4j (via `Neo4jVector`).
    

A **tool-enabled agent** (ReAct pattern) orchestrates between these two pipelines, deciding when to use graph queries, when to use review retrieval, or when to combine both.

----------

## 🏗️ Architecture



```mermaid
flowchart LR
  subgraph Data
    CSV[Hospital CSV Data]
    Neo4j[Neo4j AuraDB (Graph + Vector Index)]
  end

  subgraph Pipelines
    ReviewChain[Review Vector Chain]
    CypherChain[Cypher QA Chain]
    Agent[RAG Agent (ReAct Tools)]
  end

  subgraph Interfaces
    API[FastAPI Backend (/chat)]
    UI[Streamlit UI]
  end

  CSV --> ETL[ETL Script] --> Neo4j
  Neo4j --> ReviewChain
  Neo4j --> CypherChain
  ReviewChain --> Agent
  CypherChain --> Agent
  Agent --> API --> UI

```

### 🔎 Components in Detail

#### 1. ETL (Data Ingestion into Neo4j)

-   **Input**: Hospital CSVs (hospitals, physicians, patients, visits, reviews, payers).
    
-   **Nodes created**: `Hospital`, `Physician`, `Patient`, `Visit`, `Review`, `Payer`.
    
-   **Relationships modeled**:
    
    -   `(Patient)-[:HAS]->(Visit)`
        
    -   `(Visit)-[:AT]->(Hospital)`
        
    -   `(Physician)-[:TREATS]->(Visit)`
        
    -   `(Visit)-[:COVERED_BY]->(Payer)`
        
    -   `(Visit)-[:WRITES]->(Review)`
        
-   Uniqueness constraints on IDs ensure repeatable loads.
    
-   Review embeddings generated with Gemini embedding model (`text-embedding-004`) and stored on `Review` nodes.
    
-   This step converts tabular CSVs into a knowledge graph enriched with embeddings, enabling both symbolic (Cypher) and semantic (vector) retrieval.
    

#### 2. Review Vector Chain (Semantic QA)

-   Built with `Neo4jVector` as the vector store, retrieving from `Review` nodes by cosine similarity.
    
-   Retriever fetches top-k similar reviews (k=12).
    
-   Uses retrieval-augmented prompting:
    
    -   Injects retrieved review snippets into a Gemini-powered LLM (`HOSPITAL_QA_MODEL`) via `ChatPromptTemplate`.
        
    -   LLM is forced to ground answers in retrieved context, or say “I don’t know” if insufficient evidence.
        
-   **Example query**:
    
    > "What do patients say about Dr. Smith?"
    
    → Retrieves review texts mentioning Dr. Smith, synthesizes them into a natural response.
    

#### 3. Cypher QA Chain (Structured QA)

-   Uses two coordinated LLMs (both Gemini models):
    
    -   **Cypher generator**: Maps natural language → Cypher queries, guided by schema, strict instructions, and example queries.
        
    -   **Answer synthesizer**: Converts raw Cypher results into fluent, human-readable answers.
        
-   Prompt engineering enforces:
    
    -   No database writes/deletes.
        
    -   Use of `IS NULL` for missing data.
        
    -   Aliasing (`WITH v as visit, ...`) for clarity.
        
    -   Schema-specific constraints (e.g., allowed states, test result categories).
        
-   **Example query**:
    
    > "Which hospital has the most visits?"
    
    → **Cypher**:
    
    Cypher
    
    ```
    MATCH (h:Hospital)<-[:AT]-(v:Visit)
    RETURN h.name AS HospitalName, COUNT(v) AS VisitCount
    ORDER BY VisitCount DESC
    LIMIT 1
    
    ```
    
    → **Answer**: "Richardson-Powell hospital has the most visits, with 387 visits."
    

#### 4. RAG Agent (Tool-enabled Orchestration)

-   Built using `initialize_agent` with `AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION`.
    
-   **Tools registered**:
    
    -   `HospitalReviewQA` (review vector chain)
        
    -   `HospitalGraphQA` (cypher chain)
        
-   Implements ReAct reasoning pattern:
    
    -   Thought → Action → Observation → Final Answer.
        
-   Dynamically selects the right chain (or both).
    
-   **Example query**:
    
    > "Which hospital has the most visits, and what do patients say about it?"
    
-   Agent first calls Cypher QA to find the hospital.
    
-   Then calls Review Vector QA scoped to that hospital.
    
-   Synthesizes a multi-source answer.
    

#### 5. FastAPI Backend

-   Exposes `/chat` endpoint:
    
    -   Accepts JSON with a `"question"`.
        
    -   Passes question to the RAG agent.
        
    -   Returns structured JSON response.
        
-   Acts as a clean API boundary between the model layer and the UI.
    
-   Swagger docs auto-available at `/docs`.
    

#### 6. Streamlit UI

-   Simple web UI to interact with the chatbot.
    
-   Reads `API_URL` from `.env` so it can target:
    
    -   `http://localhost:8000/chat` when local.
        
    -   `http://api:8000/chat` when running via Docker Compose.
        
-   Displays responses inline.
    
-   **Example**:
    
    > You: Which hospital has the most visits?
    > 
    > Bot: Richardson-Powell hospital has the most visits, with 387 visits.
    

#### 7. Docker Compose Deployment

-   **ETL Service**: Loads Neo4j with CSVs.
    
-   **API Service**: Serves FastAPI (`uvicorn`).
    
-   **UI Service**: Runs Streamlit (`streamlit run`).
    
-   **Inter-service communication**:
    
    -   UI → API via service name `http://api:8000/chat`.
        
    -   API → Neo4j AuraDB via credentials in `.env`.
        
-   All services run in isolation but networked via Docker.
    

----------

### 🚀 Why This Matters

This project demonstrates:

-   **Hybrid RAG architecture** — semantic retrieval + structured reasoning in one agent.
    
-   **Knowledge Graph + LLM synergy** — using Neo4j to ground LLMs with schema-aware Cypher queries.
    
-   **Production-readiness** — containerized with Docker Compose, modular FastAPI backend, UI frontend.
    
-   **LLM orchestration** — ReAct agent combining tools dynamically.
    

