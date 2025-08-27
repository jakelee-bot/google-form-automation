from flask import Flask, render_template_string, request, jsonify
import asyncio
import json
import os
from src.form_automation import GoogleFormBot, MessageParser

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Form Automation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            width: 100%;
            max-width: 600px;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            text-align: center;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .form-container {
            padding: 40px;
        }
        
        .form-group {
            margin-bottom: 30px;
        }
        
        label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #333;
            font-size: 1.1em;
        }
        
        textarea {
            width: 100%;
            min-height: 250px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            font-family: 'Monaco', 'Menlo', monospace;
            transition: all 0.3s ease;
            background: #f8f9fa;
            resize: vertical;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
            background: white;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 18px 40px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            position: relative;
            overflow: hidden;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            margin-top: 30px;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            animation: slideIn 0.5s ease;
        }
        
        .success {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: #1a5f3f;
        }
        
        .error {
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: #721c24;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid white;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s linear infinite;
            margin-right: 10px;
            vertical-align: middle;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .example {
            background: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            font-size: 0.9em;
            color: #666;
            margin-top: 10px;
        }
        
        @media (max-width: 600px) {
            .header h1 {
                font-size: 2em;
            }
            
            .form-container {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Form Automation</h1>
            <p>Automatically fill your Google Form in seconds</p>
        </div>
        
        <div class="form-container">
            <form method="POST" action="/submit" id="automationForm">
                <div class="form-group">
                    <label for="message">Paste your form details:</label>
                    <textarea name="message" id="message" placeholder="Your name: John Doe
Your email: john@example.com
Organization name: Acme Corp
Organization sector: Academic
How many people need Premium access? 5
Length of license: 1" required></textarea>
                    <div class="example">
                        💡 Tip: Use the exact format shown above for best results
                    </div>
                </div>
                
                <button type="submit" id="submitBtn">
                    <span id="btnText">Fill Form Automatically</span>
                </button>
            </form>
            
            {% if status %}
            <div class="status {{ status_type }}">
                {{ status }}
            </div>
            {% endif %}
        </div>
    </div>
    
    <script>
    document.getElementById('automationForm').addEventListener('submit', function(e) {
        const btn = document.getElementById('submitBtn');
        const btnText = document.getElementById('btnText');
        btn.disabled = true;
        btnText.innerHTML = '<span class="loading"></span>Processing...';
    });
    
    // Auto-resize textarea
    const textarea = document.getElementById('message');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/submit', methods=['POST'])
def submit():
    message = request.form.get('message', '')
    
    try:
        # Create new event loop for thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_automation():
            bot = GoogleFormBot(headless=True, page_by_page=False)
            try:
                await bot.setup()
                await bot.run_automation(message)
                await bot.cleanup()
                return True, "✅ Form submitted successfully! The automation has filled out your Google Form."
            except Exception as e:
                print(f"Automation error: {str(e)}")
                return False, f"❌ Error: {str(e)}"
        
        success, status = loop.run_until_complete(run_automation())
        loop.close()
        
        return render_template_string(
            HTML_TEMPLATE, 
            status=status,
            status_type='success' if success else 'error'
        )
    except Exception as e:
        print(f"Route error: {str(e)}")
        return render_template_string(
            HTML_TEMPLATE, 
            status=f"❌ Server error: {str(e)}",
            status_type='error'
        )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)