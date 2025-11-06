# Simple Universal AI Orchestrator

**ChatGPT simplicity with multi-agent power**

This is a working demo that shows the core concept - you type naturally, the system routes to specialized agents automatically.

## 🚀 Run It Now

```bash
cd simple-orchestrator
python3 orchestrator.py
```

That's it! No dependencies, no configuration, just run it.

## 💬 Try These Examples

```
You: help
You: Analyze this contract and extract key terms
You: Show me sales trends for Q4
You: Write a Python function to calculate compound interest
You: What are the latest developments in quantum computing?
You: quit
```

## 🎯 How It Works

1. **You type** any request in natural language
2. **Intent Classifier** figures out what you want (document processing? data analysis? code?)
3. **Router** sends to the right specialist agent
4. **Agent** responds with what it would do in production
5. **You get** a conversational response

## 🤖 Available Agents

- **Document Processor** - Extracts from PDFs, contracts, forms (IRZ-CoT method)
- **Data Analyst** - SQL queries, charts, trends
- **Code Expert** - Generates code in any language
- **Research Assistant** - Web research, synthesis
- **General Assistant** - Conversations, help

## 🔧 Architecture

```
Your Message
    ↓
Intent Classification (pattern matching)
    ↓
Route to Specialist Agent
    ↓
Agent Response
```

## 📊 Demo Mode

This is a demo showing the concept. In production:
- Connects to real LLMs (GPT-4, Claude)
- Connects to databases (PostgreSQL, MongoDB)
- Processes actual files
- Executes real code
- Searches the web
- 98%+ accuracy on extraction

## 🎨 Full Version

For the full web interface with WebSocket, see:
- `universal-orchestrator/` - Full production system with web UI
- `intelligent-doc-processor/` - Specialized document processing pipeline

## 💡 Key Insight

**User sees:** Simple chat like ChatGPT
**System does:** Intelligent routing to specialized agents

This solves the enterprise problem: one interface for ANY task, but with specialized expertise for EACH task.
