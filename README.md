# Archon 🏛️ (FastAPI Edition)
### AI-Native Distributed System Design Interview & Evaluation Platform

[![FastAPI Version](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python Version](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis)](https://redis.io)
[![Apache Kafka](https://img.shields.io/badge/Kafka-3.7-231F20?style=flat-square&logo=apachekafka)](https://kafka.apache.org)
[![OpenTelemetry](https://img.shields.io/badge/Observability-OpenTelemetry-F5A800?style=flat-square&logo=opentelemetry)](https://opentelemetry.io)

---

## 📌 Overview

**Archon FastAPI** is an enterprise-grade, end-to-end reimplementation of the Archon System Design Interview platform, rewritten completely in **Python & FastAPI**.

Combining asynchronous high-performance I/O, domain-driven design (DDD), real-time interactive whiteboards over WebSockets, transactional event streaming (Outbox + Kafka), multi-provider LLM orchestration (Gemini, Groq, NVIDIA), and vector knowledge search (Qdrant), Archon conducts and evaluates Senior and Staff-level System Design interviews with rigorous technical fidelity.

---

## 🏛️ System Architecture

```mermaid
flowchart TB
    subgraph Clients["Candidate Client Tier"]
        CLI["Rich Interactive Terminal CLI (Typer)"]
        Browser["React / Next.js Web App"]
    end

    subgraph Edge["FastAPI Gateway & Ingress"]
        API["FastAPI Async Gateway (Uvicorn / Starlette)"]
        RateLimiter["Sliding Window Log Limiter (Redis Lua)"]
        Tracer["OpenTelemetry W3C Tracing"]
        Metrics["Prometheus Collector (/metrics)"]
    end

    subgraph Persistence["Storage & Caching Tier"]
        Postgres[("PostgreSQL 15 / SQLite (Async SQLAlchemy)")]
        RedisCache[("Redis 7 (Session Store, L2 Cache, Pub/Sub)")]
        QdrantDB[("Qdrant (Vector Knowledge Base)")]
    end

    subgraph EventStream["Distributed Event Backbone & CDC"]
        OutboxWorker["Transactional Outbox Worker"]
        Kafka{{"Apache Kafka 3.7"}}
        DLQ["Dead Letter Queue (DLQ)"]
    end

    subgraph AIWorker["Intelligence & Evaluation Layer"]
        FSM["Interview FSM (Requirements -> Estimation -> Architecture -> Evaluation)"]
        Rotator["LLM Key Rotator (Gemini / Groq / NVIDIA)"]
        Evaluator["5-Dimensional Evaluation & Scoring Engine"]
    end

    Browser <-->|WebSocket / REST| API
    CLI <-->|REST & CLI Client| API
    API --> RateLimiter
    API --> Tracer
    API --> Postgres
    API <--> RedisCache
    Postgres --> OutboxWorker
    OutboxWorker --> Kafka
    Kafka --> Evaluator
    Evaluator --> Postgres
    API <--> FSM
    FSM --> Rotator
```

---

## ⚙️ Core Engines & Bounded Contexts

1. **Authentication & Identity (`app/domains/auth`)**:
   - Secure bcrypt password hashing, JWT with token versioning, revocation, and OAuth2.
2. **Interview Lifecycle Engine (`app/domains/interview`)**:
   - Manages candidate sessions, time limits, question selection, and phase transitions.
3. **Interactive Whiteboard & Context Fusion (`app/domains/diagram`)**:
   - Real-time nodes and edges streaming over WebSockets, converting architectural diagrams into LLM prompts.
4. **AI Socratic Interviewer & FSM (`app/domains/ai`)**:
   - Multi-agent conversational FSM (`REQUIREMENTS` $	o$ `ESTIMATION` $	o$ `HIGH_LEVEL` $	o$ `DEEP_DIVE` $	o$ `COMPLETED`).
5. **Evaluation & Scorecard Engine (`app/domains/reports`)**:
   - Scores candidates across 5 core dimensions: Requirements, Estimation, Architecture, Data Modeling, and Scalability.
6. **Quiz Bank & Daily Architecture Challenge (`app/domains/quiz`)**:
   - Two-tier cached quiz decks with instant answer verification and explanations.
7. **Candidate Intelligence & Analytics (`app/domains/analytics`, `app/domains/dashboard`)**:
   - 5-axis radar charts, readiness scores, and streak tracking.

---

## ⚡ Quick Start

### 1. Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Seed Database
```bash
python -m app.cli seed
```

### 3. Run FastAPI Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 4. Interactive CLI Testing
```bash
# List available system design questions
python -m app.cli questions

# Register a candidate
python -m app.cli register "Agrim Dubey" "agrimdubey37@gmail.com" "SecurePass123!"

# Start an interview session
python -m app.cli start q-whatsapp-01

# View quiz decks and daily challenge
python -m app.cli quiz
```

### 5. Run Test Suite
```bash
pytest tests/ -v
```

---

## 🧪 Testing

The repository includes a comprehensive automated test suite testing all endpoints, authentication, diagram synchronization, quiz evaluation, and CLI operations:
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 📜 Authorship & License

Developed with clean code practices by **Agrim Dubey** (`agrimdubey37@gmail.com`).
Licensed under the MIT License.
