"""Research Chat API endpoints"""

from typing import List, Optional
import uuid
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.workflows.research_workflow import research_workflow
from app.core.deps import get_db, get_current_user
from app.models.user import User


router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""

    role: str  # "user" or "assistant"
    content: str


class ResearchChatRequest(BaseModel):
    """Request model for research chat"""

    message: str
    chat_history: Optional[List[ChatMessage]] = None


@router.post("/chat")
async def research_chat(
    request: ResearchChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Research Chat endpoint with Server-Sent Events (SSE)

    Process user question through multi-agent workflow and stream results in real-time

    Args:
        request: ResearchChatRequest with message and optional chat_history
        db: Database session for recording agent executions
        current_user: Current authenticated user (optional)

    Returns:
        StreamingResponse with SSE events
    """
    try:
        # Generate conversation ID for tracking
        conversation_id = str(uuid.uuid4())

        # Research chat doesn't require authentication
        user_id = None

        # Convert chat history to dict format
        chat_history = []
        if request.chat_history:
            chat_history = [
                {"role": msg.role, "content": msg.content}
                for msg in request.chat_history
            ]

        # Process question through workflow
        async def event_generator():
            """Generate SSE events from workflow"""
            try:
                async for event in research_workflow.process_question(
                    user_message=request.message,
                    chat_history=chat_history,
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id,
                ):
                    # Format as SSE
                    event_data = json.dumps(event, ensure_ascii=False)
                    yield f"data: {event_data}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                # Send error event
                error_event = {
                    "type": "error",
                    "data": {"error": str(e), "message": "处理请求时发生错误"},
                }
                yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-agents")
async def get_available_agents():
    """
    Get list of available business agents

    Returns:
        List of agent information
    """
    from app.agents.registry import agent_registry

    available_agents = agent_registry.get_available_agents()

    return {
        "agents": [
            {
                "name": agent.name,
                "display_name": agent.display_name,
                "description": agent.description,
                "specialization": agent.specialization,
                "is_available": agent.is_available,
            }
            for agent in available_agents
        ]
    }
