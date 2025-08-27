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
    <title>Form Automation Suite</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            min-height: 100vh;
            color: #ffffff;
            overflow-x: hidden;
        }
        
        /* Animated gradient background */
        .gradient-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(125deg, #0a0a0a 0%, #1a1a1a 25%, #2d2d2d 50%, #1a1a1a 75%, #0a0a0a 100%);
            background-size: 400% 400%;
            animation: gradient-shift 15s ease infinite;
            z-index: -2;
        }
        
        .noise {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.02;
            z-index: -1;
            pointer-events: none;
            background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMzAwIj48ZmlsdGVyIGlkPSJhIj48ZmVUdXJidWxlbmNlIGJhc2VGcmVxdWVuY3k9Ii43NSIgbnVtT2N0YXZlcz0iMTAiLz48L2ZpbHRlcj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWx0ZXI9InVybCgjYSkiIG9wYWNpdHk9IjEiLz48L3N2Zz4=');
        }
        
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 60px 20px;
            position: relative;
            z-index: 1;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 24px;
            padding: 48px;
            box-shadow: 
                0 0 0 1px rgba(255, 255, 255, 0.1) inset,
                0 20px 40px rgba(0, 0, 0, 0.5);
        }
        
        .header {
            text-align: center;
            margin-bottom: 48px;
        }
        
        h1 {
            font-size: 3.5rem;
            font-weight: 200;
            letter-spacing: -0.02em;
            margin-bottom: 16px;
            background: linear-gradient(135deg, #ffffff 0%, #888888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            font-size: 1.125rem;
            color: rgba(255, 255, 255, 0.6);
            font-weight: 300;
        }
        
        .form-group {
            margin-bottom: 32px;
        }
        
        label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        textarea {
            width: 100%;
            min-height: 300px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px;
            font-size: 15px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            color: rgba(255, 255, 255, 0.9);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            resize: vertical;
        }
        
        textarea:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.04);
            box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.05);
        }
        
        textarea::placeholder {
            color: rgba(255, 255, 255, 0.3);
        }
        
        button {
            position: relative;
            width: 100%;
            padding: 20px 32px;
            font-size: 16px;
            font-weight: 500;
            letter-spacing: 0.025em;
            color: #000000;
            background: linear-gradient(135deg, #ffffff 0%, #e0e0e0 100%);
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }
        
        button::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, transparent 0%, rgba(255, 255, 255, 0.2) 50%, transparent 100%);
            transform: translateX(-100%);
            transition: transform 0.6s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255, 255, 255, 0.1);
        }
        
        button:hover::before {
            transform: translateX(100%);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            margin-top: 32px;
            padding: 20px 24px;
            border-radius: 12px;
            font-size: 15px;
            line-height: 1.6;
            animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .success {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.2);
            color: #10b981;
        }
        
        .error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }
        
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(0, 0, 0, 0.2);
            border-radius: 50%;
            border-top-color: #000000;
            animation: spin 1s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .hint {
            margin-top: 16px;
            padding: 16px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .hint-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: rgba(255, 255, 255, 0.5);
            margin-bottom: 8px;
        }
        
        .hint-text {
            font-size: 13px;
            color: rgba(255, 255, 255, 0.4);
            line-height: 1.5;
        }
        
        @media (max-width: 640px) {
            h1 {
                font-size: 2.5rem;
            }
            
            .card {
                padding: 32px 24px;
            }
        }
    </style>
</head>
<body>
    <div class="gradient-bg"></div>
    <div class="noise"></div>
    
    <div class="container">
        <div class="card">
            <div class="header">
                <h1>Form Automation</h1>
                <p class="subtitle">Professional form filling powered by advanced automation</p>
            </div>
            
            <form method="POST" action="/submit" id="automationForm">
                <div class="form-group">
                    <label for="message">Form Data Input</label>
                    <textarea 
                        name="message" 
                        id="message" 
                        placeholder="Your name: John Doe
Your email: john@example.com
Organization name: Acme Corporation
Organization sector: Industry
How many people need Premium access? 5
Length of license: 2" 
                        required
                        spellcheck="false"
                    ></textarea>
                    
                    <div class="hint">
                        <div class="hint-title">Input Format</div>
                        <div class="hint-text">Each field should be on a new line with the format: Field name: Value</div>
                    </div>
                </div>
                
                <button type="submit" id="submitBtn">
                    <span id="btnText">Execute Automation</span>
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
        btnText.innerHTML = '<span class="loading"></span>Processing Request';
    });
    
    // Auto-resize textarea
    const textarea = document.getElementById('message');
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 500) + 'px';
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_automation():
            bot = GoogleFormBot(headless=True, page_by_page=False)
            try:
                await bot.setup()
                await bot.run_automation(message)
                await bot.cleanup()
                return True, "Form successfully submitted. The automation has completed the Google Form filling process."
            except Exception as e:
                print(f"Automation error: {str(e)}")
                return False, f"Automation failed: {str(e)}"
        
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
            status=f"System error: {str(e)}",
            status_type='error'
        )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)