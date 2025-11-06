"""
Web Server
FastAPI server with ChatGPT-like web interface
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict
import uuid
import json

from ..core.orchestrator import UniversalOrchestrator

app = FastAPI(title="Universal AI Orchestrator", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
templates = Jinja2Templates(directory="src/ui/templates")

# Initialize orchestrator
orchestrator = UniversalOrchestrator()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agents": len(orchestrator.agent_registry.list_agents())}


@app.get("/api/capabilities")
async def get_capabilities():
    """Get list of system capabilities"""
    return {"capabilities": orchestrator.list_capabilities()}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    active_connections[client_id] = websocket

    # Get or create conversation
    conversation_id = None

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message")
            conversation_id = message_data.get("conversation_id")

            # Process message through orchestrator
            response = await orchestrator.process_message(
                user_message=user_message,
                conversation_id=conversation_id,
                user_id=client_id
            )

            # Send response back to client
            await websocket.send_json(response)

    except WebSocketDisconnect:
        if client_id in active_connections:
            del active_connections[client_id]
    except Exception as e:
        error_response = {
            "error": str(e),
            "message": "An error occurred processing your request."
        }
        await websocket.send_json(error_response)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
