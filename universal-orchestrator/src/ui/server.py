"""
Web Server
FastAPI server for Financial Corpus Analyzer with file upload, URL scraping, and alpha extraction
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict, List
from pydantic import BaseModel
import uuid
import json
import os
import aiofiles
from pathlib import Path

from ..core.orchestrator import UniversalOrchestrator

app = FastAPI(title="Financial Corpus Analyzer", version="2.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/ui/static"), name="static")
templates = Jinja2Templates(directory="src/ui/templates")

# Initialize orchestrator
orchestrator = UniversalOrchestrator()

# Active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# File storage
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory storage for uploaded files and scraped data
uploaded_files_db = {}
scraped_urls_db = {}


class URLScrapeRequest(BaseModel):
    url: str


class ReportGenerationRequest(BaseModel):
    files: List[str]
    urls: List[str]
    conversation_id: str = None


@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """Serve main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agents": len(orchestrator.agent_registry.list_agents()),
        "uploaded_files": len(uploaded_files_db),
        "scraped_urls": len(scraped_urls_db)
    }


@app.get("/api/capabilities")
async def get_capabilities():
    """Get list of system capabilities"""
    return {"capabilities": orchestrator.list_capabilities()}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload"""
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        stored_filename = f"{file_id}{file_extension}"
        file_path = UPLOAD_DIR / stored_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Store metadata
        uploaded_files_db[file_id] = {
            "id": file_id,
            "original_name": file.filename,
            "stored_path": str(file_path),
            "size": len(content),
            "content_type": file.content_type
        }

        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/scrape")
async def scrape_url(request: URLScrapeRequest):
    """Scrape content from URL"""
    try:
        import requests
        from bs4 import BeautifulSoup

        # Fetch URL content
        response = requests.get(request.url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else request.url

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text_content = soup.get_text()

        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = '\n'.join(chunk for chunk in chunks if chunk)

        # Generate scrape ID
        scrape_id = str(uuid.uuid4())

        # Store scraped content
        scraped_urls_db[scrape_id] = {
            "id": scrape_id,
            "url": request.url,
            "title": title_text,
            "content": text_content,
            "length": len(text_content)
        }

        return {
            "success": True,
            "scrape_id": scrape_id,
            "title": title_text,
            "url": request.url,
            "length": len(text_content)
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/generate-report")
async def generate_report(request: ReportGenerationRequest):
    """Generate comprehensive alpha report from uploaded files and scraped URLs"""
    try:
        # Collect all content
        corpus_content = []

        # Add uploaded files
        for file_id in request.files:
            if file_id in uploaded_files_db:
                file_info = uploaded_files_db[file_id]
                file_path = file_info["stored_path"]

                # Read file content (basic text extraction)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        corpus_content.append({
                            "source": file_info["original_name"],
                            "type": "file",
                            "content": content
                        })
                except:
                    pass

        # Add scraped URLs
        for url_id in request.urls:
            if url_id in scraped_urls_db:
                url_info = scraped_urls_db[url_id]
                corpus_content.append({
                    "source": url_info["title"],
                    "type": "url",
                    "content": url_info["content"]
                })

        if not corpus_content:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "No data available for report generation"}
            )

        # Generate comprehensive report using orchestrator
        report_prompt = f"""
        You are a senior financial analyst tasked with analyzing a large corpus of financial data.
        You have access to {len(corpus_content)} data sources.

        Your task:
        1. Analyze ALL the provided data comprehensively
        2. Extract ALL alpha opportunities (investment insights, competitive advantages, market inefficiencies)
        3. Identify key financial trends, risks, and opportunities
        4. Create a coherent, well-structured report

        Data sources:
        {json.dumps([{"source": item["source"], "type": item["type"], "length": len(item["content"])} for item in corpus_content], indent=2)}

        Combined content (analyze thoroughly):
        {"="*80}
        {chr(10).join([f"SOURCE: {item['source']}\n{item['content']}\n{'-'*80}" for item in corpus_content])}
        {"="*80}

        Generate a comprehensive HTML report with:
        - Executive Summary
        - Key Alpha Opportunities (ranked by strength)
        - Financial Analysis
        - Risk Assessment
        - Strategic Recommendations

        Format the output as clean HTML with proper headings and formatting.
        """

        # Process through orchestrator
        response = await orchestrator.process_message(
            user_message=report_prompt,
            conversation_id=request.conversation_id,
            user_id="report_generator"
        )

        # Extract alpha insights using advanced prompt
        alpha_prompt = f"""
        Analyze this financial corpus and extract ONLY the highest-quality alpha opportunities.
        Alpha = investment insights that provide a competitive advantage or market edge.

        Return a JSON array of alpha insights with this EXACT structure:
        [
            {{
                "strength": "strong|moderate|weak",
                "score": 1-10,
                "title": "Brief title",
                "description": "Clear description",
                "rationale": "Why this is alpha",
                "evidence": "Supporting evidence from data"
            }}
        ]

        Criteria for alpha:
        - Strong (8-10): High-probability market opportunities, unique insights, significant competitive advantages
        - Moderate (5-7): Interesting opportunities with some validation needed
        - Weak (1-4): Speculative ideas or minor insights

        Data to analyze:
        {chr(10).join([f"{item['source']}: {item['content'][:1000]}..." for item in corpus_content])}

        Return ONLY valid JSON array, no markdown, no explanation.
        """

        alpha_response = await orchestrator.process_message(
            user_message=alpha_prompt,
            conversation_id=request.conversation_id,
            user_id="alpha_extractor"
        )

        # Parse alpha insights
        try:
            # Extract JSON from response
            alpha_text = alpha_response.get("message", "[]")
            # Remove markdown code blocks if present
            if "```" in alpha_text:
                alpha_text = alpha_text.split("```json")[1].split("```")[0] if "```json" in alpha_text else alpha_text.split("```")[1].split("```")[0]

            alpha_insights = json.loads(alpha_text.strip())
        except:
            # Fallback: create sample insights
            alpha_insights = [
                {
                    "strength": "moderate",
                    "score": 6,
                    "title": "Data Analysis Required",
                    "description": "Upload more financial data for detailed alpha extraction",
                    "rationale": "Insufficient data for comprehensive analysis",
                    "evidence": "Limited corpus size"
                }
            ]

        return {
            "success": True,
            "report": response.get("message", "Report generation in progress..."),
            "alpha_insights": alpha_insights,
            "sources_analyzed": len(corpus_content)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


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
            context = message_data.get("context", {})

            # Add context about uploaded files and scraped URLs
            if context.get("has_data"):
                context_info = []
                for file_id in context.get("files", []):
                    if file_id in uploaded_files_db:
                        context_info.append(f"File: {uploaded_files_db[file_id]['original_name']}")

                for url_id in context.get("urls", []):
                    if url_id in scraped_urls_db:
                        context_info.append(f"URL: {scraped_urls_db[url_id]['title']}")

                if context_info:
                    user_message = f"[Context: You have access to {', '.join(context_info)}]\n\n{user_message}"

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
        import traceback
        traceback.print_exc()
        error_response = {
            "error": str(e),
            "message": "An error occurred processing your request."
        }
        await websocket.send_json(error_response)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
