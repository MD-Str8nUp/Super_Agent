import os
import asyncio
import logging
import json
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import openai
import requests
from typing import Dict, Any

# Import your agent functions
from web_functions import (
    create_notion_task_web, check_ndis_compliance_web, query_business_data_web,
    manage_msa_enrollment_web, generate_invoice_web, add_calendar_event_web, send_email_web,
    create_google_calendar_event_web, get_upcoming_events_web, read_recent_emails_web,
    send_gmail_web, check_calendar_availability_web
)
from ops import SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ops-py-secret-key-12345")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Handle Google credentials for production
def setup_google_credentials():
    """Setup Google credentials from environment variable"""
    try:
        if os.getenv("GOOGLE_CREDENTIALS_BASE64"):
            # Decode base64 credentials
            credentials_json = base64.b64decode(os.getenv("GOOGLE_CREDENTIALS_BASE64")).decode('utf-8')
            # Write to temporary file
            with open('/tmp/google-credentials.json', 'w') as f:
                f.write(credentials_json)
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/google-credentials.json'
        elif os.path.exists('google-credentials.json'):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials.json'
    except Exception as e:
        logger.error(f"Error setting up Google credentials: {e}")

# Setup credentials on startup
setup_google_credentials()

class OPSAgentUI:
    def __init__(self):
        self.conversation_history = []
        self.agent_status = "Ready"
        
    async def chat_with_agent(self, user_message: str) -> str:
        """Send message to OPS.PY agent and get response"""
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user", 
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Create OpenAI chat completion
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + [{"role": msg["role"], "content": msg["content"]} 
                 for msg in self.conversation_history[-10:]]  # Keep last 10 messages
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            agent_response = response.choices[0].message.content
            
            # Add agent response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": agent_response,
                "timestamp": datetime.now().isoformat()
            })
            
            return agent_response
            
        except Exception as e:
            logger.error(f"Error in chat_with_agent: {e}")
            return f"❌ Error communicating with OPS.PY: {str(e)}"
    
    def get_business_overview(self) -> Dict[str, Any]:
        """Get overview of all business operations"""
        try:
            overview = {
                "businesses": {
                    "STR8N UP": {
                        "status": "Active",
                        "priority_items": 3,
                        "upcoming_deadlines": 2
                    },
                    "CSSA": {
                        "status": "NDIS Audit Prep",
                        "priority_items": 5,
                        "upcoming_deadlines": 4
                    },
                    "MSA": {
                        "status": "Term 1 Launch",
                        "priority_items": 7,
                        "upcoming_deadlines": 3
                    }
                },
                "recent_activity": [
                    "MSA enrollment: 225 kids registered for Term 1",
                    "NDIS audit scheduled: May 14-15, 2025",
                    "Winter camp planning: 44 kids, Jan 3-5",
                    "Buddy-Up program launch preparation"
                ],
                "agent_status": self.agent_status,
                "last_updated": datetime.now().isoformat()
            }
            return overview
        except Exception as e:
            logger.error(f"Error getting business overview: {e}")
            return {"error": str(e)}

# Initialize agent UI
agent_ui = OPSAgentUI()

# Routes
@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('dashboard.html')

@app.route('/mobile')
def mobile_dashboard():
    """Mobile-optimized dashboard"""
    return render_template('mobile_dashboard.html')

@app.route('/api/overview')
def api_overview():
    """Get business overview data"""
    overview = agent_ui.get_business_overview()
    return jsonify(overview)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Chat endpoint for communicating with OPS.PY"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        # Run async function in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agent_response = loop.run_until_complete(agent_ui.chat_with_agent(user_message))
        loop.close()
        
        return jsonify({
            "response": agent_response,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat API: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/functions/<function_name>', methods=['POST'])
def execute_function(function_name):
    try:
        data = request.get_json() or {}
        if function_name == "create_task":
            result = asyncio.run(create_notion_task_web(title=data.get('title', ''), project=data.get('project', 'STR8N UP'), priority=data.get('priority', 'Medium'), due_date=data.get('due_date', ''), description=data.get('description', '')))
        elif function_name == "check_compliance":
            result = asyncio.run(check_ndis_compliance_web(area=data.get('area', 'general')))
        elif function_name == "query_business":
            result = asyncio.run(query_business_data_web(business=data.get('business', 'ALL'), data_type=data.get('data_type', 'overview')))
        elif function_name == "manage_enrollment":
            result = asyncio.run(manage_msa_enrollment_web(action=data.get('action', 'check_numbers')))
        elif function_name == "generate_invoice":
            result = asyncio.run(generate_invoice_web(client_name=data.get('client_name', ''), business=data.get('business', 'STR8N UP'), service=data.get('service', ''), amount=float(data.get('amount', 0))))
        elif function_name == "add_event":
            result = asyncio.run(add_calendar_event_web(title=data.get('title', ''), date=data.get('date', ''), time=data.get('time', ''), duration=int(data.get('duration', 60))))
        elif function_name == "send_email":
            result = asyncio.run(send_email_web(to_email=data.get('to_email', ''), subject=data.get('subject', ''), message=data.get('message', ''), cc_email=data.get('cc_email', '')))
        elif function_name == "create_google_event":
            result = asyncio.run(create_google_calendar_event_web(title=data.get('title', ''), start_datetime=data.get('start_datetime', ''), end_datetime=data.get('end_datetime', ''), description=data.get('description', ''), location=data.get('location', ''), attendees=data.get('attendees', '')))
        elif function_name == "get_upcoming_events":
            result = asyncio.run(get_upcoming_events_web(days_ahead=int(data.get('days_ahead', 7)), max_results=int(data.get('max_results', 10))))
        elif function_name == "read_emails":
            result = asyncio.run(read_recent_emails_web(max_results=int(data.get('max_results', 10)), query=data.get('query', 'is:unread')))
        elif function_name == "send_gmail":
            result = asyncio.run(send_gmail_web(to_email=data.get('to_email', ''), subject=data.get('subject', ''), body=data.get('body', ''), cc_email=data.get('cc_email', ''), bcc_email=data.get('bcc_email', '')))
        elif function_name == "check_availability":
            result = asyncio.run(check_calendar_availability_web(start_datetime=data.get('start_datetime', ''), end_datetime=data.get('end_datetime', '')))
        else: return jsonify({"error": f"Unknown function: {function_name}"}), 400
        return jsonify({"result": result, "function": function_name, "timestamp": datetime.now().isoformat()})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/conversation')
def get_conversation():
    """Get conversation history"""
    return jsonify({
        "history": agent_ui.conversation_history[-20:],  # Last 20 messages
        "count": len(agent_ui.conversation_history)
    })

@app.route('/api/status')
def get_status():
    """Get agent status"""
    return jsonify({
        "status": agent_ui.agent_status,
        "environment": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "notion_configured": bool(os.getenv("NOTION_TOKEN")),
            "deepgram_configured": bool(os.getenv("DEEPGRAM_API_KEY")),
            "cartesia_configured": bool(os.getenv("CARTESIA_API_KEY")),
            "livekit_configured": bool(os.getenv("LIVEKIT_API_KEY")),
            "google_credentials": bool(os.getenv("GOOGLE_CREDENTIALS_BASE64") or os.path.exists('google-credentials.json')),
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Main entry point for Vercel
def handler(request):
    return app(request.environ, lambda status, headers: None)

if __name__ == '__main__':
    logger.info("Starting OPS.PY Web UI...")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
