"""Whiteboard Diagram domain repository, service, and router."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_async_db
from app.core.dependencies import get_current_user
from app.models.diagram import DiagramEdge, DiagramNode
from app.models.interview import Interview
from app.models.user import User
from app.schemas.diagram import DiagramStateResponse, DiagramSyncRequest, EdgeSchema, NodeSchema

logger = logging.getLogger(__name__)


class DiagramRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_diagram_state(self, interview_id: str) -> DiagramStateResponse:
        nodes_res = await self.db.execute(select(DiagramNode).where(DiagramNode.interview_id == interview_id))
        edges_res = await self.db.execute(select(DiagramEdge).where(DiagramEdge.interview_id == interview_id))

        nodes = [NodeSchema.model_validate(n) for n in nodes_res.scalars().all()]
        edges = [EdgeSchema.model_validate(e) for e in edges_res.scalars().all()]

        return DiagramStateResponse(interview_id=interview_id, nodes=nodes, edges=edges)

    async def save_node(self, interview_id: str, node: NodeSchema) -> None:
        db_node = await self.db.get(DiagramNode, node.id)
        if db_node:
            db_node.type = node.type
            db_node.label = node.label
            db_node.x = node.x
            db_node.y = node.y
        else:
            db_node = DiagramNode(
                id=node.id, interview_id=interview_id, type=node.type, label=node.label, x=node.x, y=node.y
            )
            self.db.add(db_node)
        await self.db.commit()

    async def delete_node(self, interview_id: str, node_id: str) -> None:
        await self.db.execute(
            delete(DiagramNode).where(DiagramNode.interview_id == interview_id, DiagramNode.id == node_id)
        )
        await self.db.commit()

    async def save_edge(self, interview_id: str, edge: EdgeSchema) -> None:
        db_edge = await self.db.get(DiagramEdge, edge.id)
        if db_edge:
            db_edge.source = edge.source
            db_edge.target = edge.target
            db_edge.type = edge.type or "default"
        else:
            db_edge = DiagramEdge(
                id=edge.id, interview_id=interview_id, source=edge.source, target=edge.target, type=edge.type or "default"
            )
            self.db.add(db_edge)
        await self.db.commit()

    async def delete_edge(self, interview_id: str, edge_id: str) -> None:
        await self.db.execute(
            delete(DiagramEdge).where(DiagramEdge.interview_id == interview_id, DiagramEdge.id == edge_id)
        )
        await self.db.commit()

    async def sync_diagram(self, interview_id: str, req: DiagramSyncRequest) -> DiagramStateResponse:
        # Atomic clear and replace
        await self.db.execute(delete(DiagramEdge).where(DiagramEdge.interview_id == interview_id))
        await self.db.execute(delete(DiagramNode).where(DiagramNode.interview_id == interview_id))

        for n in req.nodes:
            self.db.add(DiagramNode(id=n.id, interview_id=interview_id, type=n.type, label=n.label, x=n.x, y=n.y))
        for e in req.edges:
            self.db.add(DiagramEdge(id=e.id, interview_id=interview_id, source=e.source, target=e.target, type=e.type or "default"))

        await self.db.commit()
        return await self.get_diagram_state(interview_id)


def diagram_to_text(state: DiagramStateResponse) -> str:
    """Architectural Context Fusion: formats whiteboard graph as textual summary for the LLM."""
    if not state.nodes:
        return "No diagram components placed on the whiteboard canvas yet."

    node_map = {n.id: f"{n.label} ({n.type})" for n in state.nodes}
    lines = ["Whiteboard Architecture Graph:"]
    lines.append("Components:")
    for n in state.nodes:
        lines.append(f" - [{n.type.upper()}] {n.label} (ID: {n.id}) at pos ({int(n.x)}, {int(n.y)})")

    if state.edges:
        lines.append("Connections:")
        for e in state.edges:
            src = node_map.get(e.source, e.source)
            tgt = node_map.get(e.target, e.target)
            lines.append(f" - {src} ---> {tgt} [Type: {e.type}]")
    else:
        lines.append("Connections: (None established yet)")

    return "\n".join(lines)


router = APIRouter(prefix="/api/v1/interviews", tags=["Diagrams"])


@router.get("/{interview_id}/diagram", response_model=DiagramStateResponse)
async def get_diagram(
    interview_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    # Verify interview ownership
    it = await db.get(Interview, interview_id)
    if not it or it.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this interview session.")

    repo = DiagramRepository(db)
    return await repo.get_diagram_state(interview_id)


@router.post("/{interview_id}/diagram/sync", response_model=DiagramStateResponse)
async def sync_diagram(
    interview_id: str,
    req: DiagramSyncRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    it = await db.get(Interview, interview_id)
    if not it or it.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this interview session.")

    repo = DiagramRepository(db)
    return await repo.sync_diagram(interview_id, req)
