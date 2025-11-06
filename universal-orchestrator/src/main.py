"""Main entry point for Universal AI Orchestrator"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.ui.server:app",
        host="0.0.0.0",
        port=3000,
        reload=True
    )
