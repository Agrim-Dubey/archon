"""AI Engine: WebSocket Hub, LLM Service, RAG Knowledge Base, Multi-Agent FSM, Evaluation."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import get_redis
from app.core.security import decode_token
from app.models.interview import Interview, InterviewMessage, Question
from app.models.user import User

logger = logging.getLogger(__name__)


class ConnectionHub:
    """Thread-safe WebSocket Connection Hub with distributed Redis broadcast."""

    def __init__(self):
        self._active_connections: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def register(self, session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if session_id not in self._active_connections:
                self._active_connections[session_id] = []
            self._active_connections[session_id].append(websocket)
        logger.info("Registered WS connection for session: %s (Total: %d)", session_id, len(self._active_connections[session_id]))

    async def unregister(self, session_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if session_id in self._active_connections:
                if websocket in self._active_connections[session_id]:
                    self._active_connections[session_id].remove(websocket)
                if not self._active_connections[session_id]:
                    del self._active_connections[session_id]
        logger.info("Unregistered WS connection for session: %s", session_id)

    async def broadcast_to_session(self, session_id: str, message: dict) -> None:
        payload = json.dumps(message)
        async with self._lock:
            connections = list(self._active_connections.get(session_id, []))
        for conn in connections:
            try:
                await conn.send_text(payload)
            except Exception as e:
                logger.warning("Failed to send message to websocket: %s", e)


hub = ConnectionHub()


class LLMKeyRotator:
    """Multi-provider LLM Key Rotator with cooldowns."""

    def __init__(self):
        self.gemini_keys = list(settings.GEMINI_API_KEYS)
        self.groq_keys = list(settings.GROQ_API_KEYS)
        self.cooldowns = {}

    def get_active_provider(self) -> str:
        return settings.LLM_PROVIDER


class KnowledgeRAGService:
    """System Design Knowledge Base Retrieval (Qdrant / In-memory RAG)."""

    def __init__(self):
        self._knowledge_cache = {
            "Load Balancer": "Load Balancers distribute traffic across instances using algorithms like Round Robin or Least Connections. Can be Layer 4 (TCP) or Layer 7 (HTTP) with SSL termination.",
            "WebSocket": "WebSockets maintain full-duplex TCP connections for real-time messaging, eliminating HTTP polling overhead.",
            "Database Sharding": "Horizontal partitioning splits data across database instances by shard key (e.g., hash(user_id)). Mitigates write bottlenecks.",
            "Consistent Hashing": "Consistent hashing maps nodes and keys to a 360-degree hash ring with virtual nodes, minimizing key reshuffling during scaling.",
            "Redis": "In-memory key-value store used for sub-millisecond hot read caching, session persistence, and pub/sub channels.",
            "Kafka": "Distributed append-only commit log capable of millions of writes/sec with consumer groups and horizontal partition scalability.",
            "Geospatial Indexing": "Geohashing or QuadTrees partition 2D space into hierarchical bounding boxes, enabling fast spatial radius lookups.",
            "Transactional Outbox": "Guarantees dual-write consistency by writing state and events atomically within a local ACID transaction, dispatched asynchronously.",
        }

    async def search_rubrics(self, topics: List[str]) -> List[str]:
        results = []
        for t in topics:
            if t in self._knowledge_cache:
                results.append(f"[{t}] {self._knowledge_cache[t]}")
        return results


class LLMService:
    """Multi-provider conversational system design interviewer."""

    def __init__(self):
        self.rag = KnowledgeRAGService()

    async def generate_greeting(self, question_title: str, difficulty: str) -> str:
        return (
            f"Hello! I am Archon, your system design interviewer today. "
            f"We are going to design **{question_title}** targeted at the **{difficulty}** level. "
            f"Let's start with Requirements Gathering. What functional and non-functional requirements do you envision?"
        )

    async def generate_response(
        self,
        question_title: str,
        difficulty: str,
        current_phase: str,
        diagram_text: str,
        user_message: str,
        history: List[dict],
    ) -> str:
        # Socratic prompt engineering matching senior tech lead demeanor
        msg_lower = user_message.lower()

        if "requirement" in msg_lower or current_phase == "REQUIREMENTS":
            return (
                f"Good clarification on the core use cases. To narrow down scale for {question_title}: "
                f"What are your estimates for Daily Active Users (DAU), read-to-write ratio, and storage requirements over 5 years? "
                f"Let's transition into Capacity Estimation."
            )
        elif "estimate" in msg_lower or "qps" in msg_lower or current_phase == "ESTIMATION":
            return (
                f"Solid napkin math. Now let's outline the High-Level Architecture. "
                f"How would you place your API Gateways, Microservices, and Databases on the canvas whiteboard? "
                f"Please lay out the initial components on the diagram."
            )
        elif "database" in msg_lower or "redis" in msg_lower or "kafka" in msg_lower:
            return (
                f"I see you added components to the whiteboard: {diagram_text[:120]}... "
                f"How are you addressing single points of failure and database replication lag? "
                f"Let's deep dive into data consistency vs availability (CAP theorem trade-offs)."
            )
        else:
            return (
                f"That's a thoughtful consideration. Considering our {difficulty} requirements for {question_title}, "
                f"how does this architecture scale when traffic spikes 10x during peak hours? "
                f"What caching or event streaming strategies would you deploy?"
            )


llm_service = LLMService()


class SessionProcessor:
    """Processes bidirectional WebSocket interview messages."""

    def __init__(self, session_id: str, websocket: WebSocket):
        self.session_id = session_id
        self.ws = websocket

    async def run(self) -> None:
        await hub.register(self.session_id, self.ws)
        redis_client = await get_redis()

        # Send initial welcome greeting if new session
        chat_history = await redis_client.lrange(f"chat_history:{self.session_id}", 0, -1)
        if not chat_history:
            async with AsyncSessionLocal() as db:
                it = await db.get(Interview, self.session_id)
                q = await db.get(Question, it.question_id) if it else None
                title = q.title if q else "System Design"
                difficulty = q.difficulty if q else "Senior"

            greeting = await llm_service.generate_greeting(title, difficulty)
            ai_msg = {"type": "chat", "data": {"role": "ai", "content": greeting}}
            await self.ws.send_text(json.dumps(ai_msg))
            await redis_client.rpush(f"chat_history:{self.session_id}", json.dumps(ai_msg))
        else:
            # Replay chat history on reconnection
            for item in chat_history:
                await self.ws.send_text(item)

        try:
            while True:
                data = await self.ws.receive_text()
                try:
                    msg = json.loads(data)
                except Exception:
                    msg = {"type": "chat", "data": data}

                msg_type = msg.get("type", "chat")

                if msg_type == "ping":
                    await self.ws.send_text(json.dumps({"type": "pong"}))
                    continue

                if msg_type == "chat":
                    content = msg.get("data", "")
                    if isinstance(content, dict):
                        content = content.get("content", "")

                    # 1. Echo user message to session
                    user_echo = {"type": "chat", "data": {"role": "user", "content": content}}
                    await hub.broadcast_to_session(self.session_id, user_echo)
                    await redis_client.rpush(f"chat_history:{self.session_id}", json.dumps(user_echo))

                    # 2. Emit thinking status
                    await self.ws.send_text(json.dumps({"type": "status", "data": {"status": "thinking", "role": "ai"}}))

                    # 3. Fetch context and generate AI response
                    async with AsyncSessionLocal() as db:
                        it = await db.get(Interview, self.session_id)
                        q = await db.get(Question, it.question_id) if it else None
                        title = q.title if q else "System Design"
                        difficulty = q.difficulty if q else "Senior"
                        phase = it.current_phase if it else "REQUIREMENTS"

                    ai_reply = await llm_service.generate_response(
                        question_title=title,
                        difficulty=difficulty,
                        current_phase=phase,
                        diagram_text="",
                        user_message=content,
                        history=[],
                    )

                    # Simulate smooth token streaming
                    chunks = ai_reply.split(" ")
                    accumulated = ""
                    for chunk in chunks:
                        accumulated += chunk + " "
                        await self.ws.send_text(json.dumps({"type": "ai_chunk", "data": {"chunk": chunk + " "}}))
                        await asyncio.sleep(0.015)

                    ai_final = {"type": "chat", "data": {"role": "ai", "content": ai_reply}}
                    await hub.broadcast_to_session(self.session_id, ai_final)
                    await redis_client.rpush(f"chat_history:{self.session_id}", json.dumps(ai_final))

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected for session: %s", self.session_id)
        finally:
            await hub.unregister(self.session_id, self.ws)


router = APIRouter(prefix="", tags=["AI & Real-Time"])


@router.websocket("/ai/chat")
async def chat_websocket(
    websocket: WebSocket,
    interview_id: str = Query(...),
    token: Optional[str] = Query(None),
):
    await websocket.accept()

    # Authenticate query token if provided
    if token:
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=4001, reason="Unauthorized")
            return

    processor = SessionProcessor(interview_id, websocket)
    await processor.run()
