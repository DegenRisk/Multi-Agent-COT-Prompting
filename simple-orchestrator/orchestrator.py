#!/usr/bin/env python3
"""
Simple Universal AI Orchestrator - Terminal Version
Just run: python orchestrator.py
"""

import json
import re
from typing import Dict, Any
from datetime import datetime


class SimpleOrchestrator:
    """Simple orchestrator that actually works"""

    def __init__(self):
        print("🚀 Universal AI Orchestrator Starting...")
        print("=" * 60)
        self.conversation_history = []

    def classify_intent(self, message: str) -> str:
        """Figure out what the user wants"""
        msg_lower = message.lower()

        # Document processing
        if any(word in msg_lower for word in ['extract', 'analyze document', 'parse', 'contract', 'pdf']):
            return 'document_processing'

        # Data analysis
        if any(word in msg_lower for word in ['analyze data', 'chart', 'graph', 'trends', 'database', 'sql']):
            return 'data_analysis'

        # Code generation
        if any(word in msg_lower for word in ['write code', 'function', 'script', 'python', 'javascript']):
            return 'code_generation'

        # Research
        if any(word in msg_lower for word in ['research', 'search', 'find information', 'what is', 'latest']):
            return 'research'

        # Default
        return 'general_conversation'

    def route_to_agent(self, intent: str, message: str) -> Dict[str, Any]:
        """Route to the right agent"""

        agents = {
            'document_processing': self.document_agent,
            'data_analysis': self.data_agent,
            'code_generation': self.code_agent,
            'research': self.research_agent,
            'general_conversation': self.general_agent
        }

        agent = agents.get(intent, self.general_agent)
        return agent(message)

    def document_agent(self, message: str) -> Dict[str, Any]:
        """Document processing specialist"""
        return {
            'agent': 'Document Processor',
            'response': f"📄 I'm the Document Processor agent. I would analyze your document using IRZ-CoT extraction.\n\n"
                       f"In production, I would:\n"
                       f"• Use OCR to extract text\n"
                       f"• Apply role-based prompting (expert analyst)\n"
                       f"• Extract key fields with reasoning\n"
                       f"• Validate against external sources (RAV/RAC)\n"
                       f"• Return structured data with 98%+ accuracy",
            'confidence': 0.95
        }

    def data_agent(self, message: str) -> Dict[str, Any]:
        """Data analysis specialist"""
        return {
            'agent': 'Data Analyst',
            'response': f"📊 I'm the Data Analyst agent. I would query your database and create visualizations.\n\n"
                       f"In production, I would:\n"
                       f"• Generate SQL queries from your request\n"
                       f"• Connect to PostgreSQL/MongoDB/etc\n"
                       f"• Analyze the data (trends, patterns, stats)\n"
                       f"• Create interactive charts (Plotly/D3.js)\n"
                       f"• Return insights and recommendations",
            'confidence': 0.92
        }

    def code_agent(self, message: str) -> Dict[str, Any]:
        """Code generation specialist"""
        # Extract what they want code for
        example_code = '''def compound_interest(principal, rate, time):
    """Calculate compound interest"""
    return principal * (1 + rate) ** time

# Example usage:
result = compound_interest(1000, 0.05, 10)
print(f"Final amount: ${result:.2f}")'''

        return {
            'agent': 'Code Expert',
            'response': f"💻 I'm the Code Expert agent. Here's what I generated:\n\n"
                       f"```python\n{example_code}\n```\n\n"
                       f"In production, I would:\n"
                       f"• Generate optimized code for any language\n"
                       f"• Include tests and documentation\n"
                       f"• Execute code in sandboxed environment\n"
                       f"• Debug and fix issues automatically",
            'confidence': 0.97
        }

    def research_agent(self, message: str) -> Dict[str, Any]:
        """Research specialist"""
        return {
            'agent': 'Research Assistant',
            'response': f"🔍 I'm the Research Assistant. I would search the web and synthesize findings.\n\n"
                       f"In production, I would:\n"
                       f"• Search multiple sources (Google, academic databases)\n"
                       f"• Extract relevant information\n"
                       f"• Synthesize into coherent summary\n"
                       f"• Cite all sources\n"
                       f"• Provide latest developments and trends",
            'confidence': 0.90
        }

    def general_agent(self, message: str) -> Dict[str, Any]:
        """General conversation"""
        return {
            'agent': 'General Assistant',
            'response': f"👋 I'm the General Assistant. I can help you with:\n\n"
                       f"• Document Processing - Extract data from PDFs, contracts, forms\n"
                       f"• Data Analysis - Query databases, create charts, find trends\n"
                       f"• Code Generation - Write code in any language\n"
                       f"• Research - Search web, synthesize information\n\n"
                       f"What would you like to do?",
            'confidence': 0.85
        }

    def process_message(self, message: str):
        """Main processing pipeline"""
        print("\n" + "─" * 60)
        print(f"📨 You: {message}")
        print("─" * 60)

        # Step 1: Classify intent
        intent = self.classify_intent(message)
        print(f"🧠 Intent detected: {intent.replace('_', ' ').title()}")

        # Step 2: Route to agent
        result = self.route_to_agent(intent, message)

        # Step 3: Display response
        print(f"🤖 Agent: {result['agent']}")
        print(f"📈 Confidence: {result['confidence']:.0%}")
        print()
        print(result['response'])
        print()

        # Save to history
        self.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user': message,
            'intent': intent,
            'agent': result['agent'],
            'response': result['response']
        })

    def run(self):
        """Run the orchestrator"""
        print("✨ System Ready! Type 'quit' to exit, 'help' for examples\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Thanks for using Universal AI Orchestrator")
                    break

                if user_input.lower() == 'help':
                    self.show_help()
                    continue

                self.process_message(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

    def show_help(self):
        """Show example queries"""
        print("\n" + "=" * 60)
        print("📚 EXAMPLE QUERIES:")
        print("=" * 60)
        print()
        print("📄 Document Processing:")
        print("   • 'Analyze this contract and extract key terms'")
        print("   • 'Extract data from this invoice'")
        print()
        print("📊 Data Analysis:")
        print("   • 'Show me sales trends for Q4'")
        print("   • 'Create a chart of customer growth'")
        print()
        print("💻 Code Generation:")
        print("   • 'Write a Python function to calculate compound interest'")
        print("   • 'Create a JavaScript function for sorting'")
        print()
        print("🔍 Research:")
        print("   • 'What are the latest developments in quantum computing?'")
        print("   • 'Research AI trends in 2024'")
        print()
        print("=" * 60)
        print()


if __name__ == "__main__":
    orchestrator = SimpleOrchestrator()
    orchestrator.run()
