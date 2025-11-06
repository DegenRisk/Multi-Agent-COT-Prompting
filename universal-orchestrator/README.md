# Universal AI Orchestrator
## ChatGPT Simplicity with Enterprise Power

---

### One Interface. Infinite Possibilities.

**Universal AI Orchestrator** is an adaptive AI engine that provides a simple ChatGPT-like interface while intelligently routing tasks to specialized agents, tools, and data sources under the hood. Users get simplicity; you get versatility.

---

## 🎯 The Vision

**User Experience**: As simple as ChatGPT
- Type natural language requests
- Upload any file type (documents, images, data)
- Get intelligent responses
- No need to know which tool to use

**Backend Reality**: Intelligent multi-agent orchestration
- Automatic intent classification
- Task routing to specialized agents
- Multi-tool integration
- Cross-data source queries
- Adaptive learning from usage

---

## ✨ Key Features

### 🗣️ Conversational Interface
- ChatGPT-style web UI
- Natural language understanding
- Context-aware conversations
- Multi-turn dialogue support
- File upload and multimodal input

### 🤖 Intelligent Task Routing
- Automatic intent detection
- 20+ specialist agents for different tasks
- Seamless agent handoffs
- Parallel agent execution when needed
- Confidence-based routing

### 🔌 Universal Connectors
- **Data Sources**: PostgreSQL, MongoDB, S3, APIs, CSV, Excel
- **Tools**: Python execution, web search, data analysis, visualization
- **Services**: OpenAI, Anthropic, Google, AWS, Azure
- **Documents**: PDF, DOCX, images, presentations
- **Code**: GitHub, GitLab, code analysis, execution

### 🧠 Adaptive Intelligence
- Learns user preferences over time
- Remembers conversation history
- Suggests relevant actions
- Improves routing accuracy
- Personalized experience

### 🎨 Multimodal Support
- Text input and generation
- Image analysis and generation
- Document processing
- Code understanding and generation
- Data visualization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONVERSATIONAL UI LAYER                       │
│         Simple Chat Interface (Like ChatGPT)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION ENGINE                          │
│  • Intent Classifier                                             │
│  • Task Router                                                   │
│  • Workflow Coordinator                                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SPECIALIST AGENTS                             │
│  Document • Data • Code • Research • Image • Writer • SQL...     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    TOOLS & CONNECTORS                            │
│  Databases • APIs • Files • Web • AI Models • Compute            │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Example Use Cases

**"Analyze this contract"** → Document Processor Agent
**"Show Q4 sales trends"** → SQL Expert + Data Analyst + Visualizer
**"Latest in quantum computing?"** → Research Assistant
**"Write Python function for X"** → Code Expert
**[Image upload] "What's this?"** → Image Analyzer

## 🚀 Quick Start

### Using Startup Scripts (Recommended)

**macOS/Linux:**
```bash
./start.sh
```

**Windows:**
```cmd
start.bat
```

Then open: **http://localhost:8000**

### Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate it
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate.bat       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env and add your API key (OpenAI, Anthropic, or Google)

# 5. Run server
python -m src.ui.server

# 6. Open browser
# http://localhost:8000
```

### Docker (Alternative)

```bash
docker-compose up -d
# Open: http://localhost:8000
```

## 💎 NEW: Financial Corpus Analyzer

The latest version includes a **professional financial analysis interface**:

### Features
- 📁 **Drag & Drop Upload**: PDF, CSV, XLSX, DOC, TXT files
- 🔗 **URL Scraping**: Automatically extract content from financial websites
- 💎 **Alpha Extraction**: AI-powered investment insights with strength scoring
- 📊 **Report Generation**: Comprehensive analysis from large document corpuses
- 💬 **Conversational Chat**: Ask questions about your uploaded data

### UI Overview
- **Left Sidebar**: Data source management (upload files, scrape URLs, view loaded data)
- **Main Area**: Tabbed interface
  - **Chat Tab**: Conversational Q&A about your data
  - **Report Tab**: Comprehensive financial analysis reports
  - **Alpha Insights Tab**: Color-coded investment opportunities (Strong/Moderate/Weak)

See [FINANCIAL_CORPUS_ANALYZER.md](../FINANCIAL_CORPUS_ANALYZER.md) for detailed documentation.

## 💼 Perfect For

✅ Enterprise teams needing versatile AI
✅ Data analysts wanting natural language queries
✅ Developers seeking automated workflows
✅ Researchers needing multi-source intelligence
✅ Anyone who wants AI that "just works"

---

**Universal AI Orchestrator** - The last AI interface you'll ever need.
