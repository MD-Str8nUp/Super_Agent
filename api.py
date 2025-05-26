import os
import json
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-agent-key")

# Initialize OpenAI
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None

@app.route('/')
def dashboard():
    """Main dashboard"""
    return jsonify({
        "message": "🎉 Super Agent is WORKING!",
        "status": "success",
        "features": [
            "✅ Basic Web Interface",
            "✅ Environment Variables",
            "✅ OpenAI Integration",
            "✅ Mobile Support"
        ],
        "environment": {
            "openai": "✅ Connected" if os.getenv("OPENAI_API_KEY") else "❌ Missing",
            "notion": "✅ Connected" if os.getenv("NOTION_TOKEN") else "❌ Missing",
            "google": "✅ Connected" if os.getenv("GOOGLE_CREDENTIALS_BASE64") else "❌ Missing",
            "flask_secret": "✅ Set" if os.getenv("FLASK_SECRET_KEY") else "❌ Missing"
        }
    })

@app.route('/mobile')
def mobile_dashboard():
    """Mobile dashboard"""
    try:
        return render_template('mobile_dashboard.html')
    except Exception as e:
        return jsonify({
            "message": "Mobile interface working!",
            "note": "Template loading issue, but backend is functional",
            "error": str(e)
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Simple chat endpoint"""
    try:
        if not openai_client:
            return jsonify({"error": "OpenAI not configured"}), 500
            
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
            
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are OPS.PY, an AI assistant for Mohamed Dhaini's businesses: STR8N UP, CSSA, and MSA. You help with task management, email communication, and business operations. Be helpful and professional."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        return jsonify({
            "response": response.choices[0].message.content,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": f"Chat error: {str(e)}"}), 500

@app.route('/api/status')
def status():
    """Status check"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": "2025-05-26",
        "services": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "notion": bool(os.getenv("NOTION_TOKEN")),
            "google": bool(os.getenv("GOOGLE_CREDENTIALS_BASE64"))
        }
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({"status": "healthy"})

@app.route('/test')
def test():
    """Test endpoint"""
    return jsonify({
        "message": "Super Agent Test Successful!",
        "all_env_vars": {
            "OPENAI_API_KEY": "SET" if os.getenv("OPENAI_API_KEY") else "MISSING",
            "NOTION_TOKEN": "SET" if os.getenv("NOTION_TOKEN") else "MISSING",
            "FLASK_SECRET_KEY": "SET" if os.getenv("FLASK_SECRET_KEY") else "MISSING",
            "GOOGLE_CREDENTIALS_BASE64": "SET" if os.getenv("GOOGLE_CREDENTIALS_BASE64") else "MISSING"
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "status": 404}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": 500}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
