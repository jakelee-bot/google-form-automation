from flask import Flask, render_template_string, request, jsonify
import asyncio
import json
import os
from src.form_automation import GoogleFormBot
from src.parser_only import MessageParser

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BioRender Form Automation</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --biorender-blue: #0066FF;
            --biorender-blue-hover: #0052CC;
            --bg-primary: #0f0f0f;
            --bg-secondary: #1a1a1a;
            --bg-card: rgba(255, 255, 255, 0.02);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: rgba(255, 255, 255, 0.95);
            --text-secondary: rgba(255, 255, 255, 0.6);
            --text-muted: rgba(255, 255, 255, 0.4);
            --success: #10b981;
            --error: #ef4444;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }
        
        /* Grid pattern background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.01) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.01) 1px, transparent 1px);
            background-size: 50px 50px;
            z-index: -1;
        }
        
        /* Gradient orbs */
        .orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(100px);
            opacity: 0.3;
            animation: float 20s infinite ease-in-out;
        }
        
        .orb-1 {
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, var(--biorender-blue) 0%, transparent 70%);
            top: -200px;
            left: -200px;
        }
        
        .orb-2 {
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, var(--biorender-blue) 0%, transparent 70%);
            bottom: -150px;
            right: -150px;
            animation-delay: 10s;
        }
        
        @keyframes float {
            0%, 100% { transform: translate(0, 0) scale(1); }
            25% { transform: translate(100px, -100px) scale(1.1); }
            50% { transform: translate(-100px, 100px) scale(0.9); }
            75% { transform: translate(50px, 50px) scale(1.05); }
        }
        
        .container {
            max-width: 720px;
            margin: 0 auto;
            padding: 60px 20px;
            position: relative;
            z-index: 1;
        }
        
        /* Logo */
        .logo {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 48px;
            gap: 16px;
        }
        
        .logo-icon {
            width: 56px;
            height: 56px;
            background: var(--biorender-blue);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 700;
            color: white;
            box-shadow: 0 4px 20px rgba(0, 102, 255, 0.3);
        }
        
        .logo-text {
            font-size: 32px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        /* Card */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            backdrop-filter: blur(10px);
            box-shadow: 
                0 0 0 1px rgba(255, 255, 255, 0.05) inset,
                0 20px 25px -5px rgba(0, 0, 0, 0.3);
        }
        
        .card-header {
            padding: 32px;
            border-bottom: 1px solid var(--border-color);
            background: rgba(255, 255, 255, 0.01);
        }
        
        h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 15px;
        }
        
        .card-body {
            padding: 32px;
        }
        
        /* Form */
        .form-group {
            margin-bottom: 24px;
        }
        
        label {
            display: block;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
            color: var(--text-secondary);
        }
        
        textarea {
            width: 100%;
            min-height: 320px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            font-size: 14px;
            font-family: 'SF Mono', Monaco, monospace;
            color: var(--text-primary);
            transition: all 0.2s ease;
            resize: vertical;
        }
        
        textarea:hover {
            border-color: rgba(255, 255, 255, 0.15);
        }
        
        textarea:focus {
            outline: none;
            border-color: var(--biorender-blue);
            background: rgba(0, 102, 255, 0.05);
            box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.15);
        }
        
        /* Button */
        button {
            width: 100%;
            padding: 14px 24px;
            background: var(--biorender-blue);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        button:hover {
            background: var(--biorender-blue-hover);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 102, 255, 0.4);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Loading dots */
        .loading-dots {
            display: inline-flex;
            gap: 4px;
        }
        
        .loading-dots span {
            width: 6px;
            height: 6px;
            background: currentColor;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% {
                transform: scale(0);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        
        /* Status */
        .alert {
            margin-top: 24px;
            padding: 16px;
            border-radius: 8px;
            font-size: 14px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            animation: slideUp 0.3s ease;
        }
        
        .alert-success {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        
        .alert-error {
            background: rgba(239, 68, 68, 0.1);
            color: var(--error);
            border: 1px solid rgba(239, 68, 68, 0.2);
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
        }
        
        /* Template helper */
        .template-box {
            margin-top: 16px;
            padding: 16px;
            background: rgba(0, 102, 255, 0.05);
            border: 1px solid rgba(0, 102, 255, 0.1);
            border-radius: 8px;
            font-size: 12px;
            color: var(--text-muted);
        }
        
        .template-box details {
            cursor: pointer;
        }
        
        .template-box summary {
            font-weight: 500;
            margin-bottom: 8px;
            color: var(--text-secondary);
        }
        
        .template-content {
            font-family: 'SF Mono', Monaco, monospace;
            line-height: 1.8;
            white-space: pre-line;
        }
    </style>
</head>
<body>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    
    <div class="container">
        <div class="logo">
            <div class="logo-icon">B</div>
            <div class="logo-text">Form Automation</div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <h1>Automate Your Google Form</h1>
                <p class="subtitle">Fill out forms instantly with our advanced automation system</p>
            </div>
            
            <div class="card-body">
                <form method="POST" action="/submit" id="automationForm">
                    <div class="form-group">
                        <label for="message">Enter your form details</label>
                        <textarea 
                            name="message" 
                            id="message" 
                            placeholder="Your name: John Doe
Your email: john@example.com
Organization name: Acme Corporation
Organization sector: Industry
How many people need Premium access?: 5
Length of license (in years): 2" 
                            required
                            spellcheck="false"
                        ></textarea>
                        
                        <div class="template-box">
                            <details>
                                <summary>📋 View complete template</summary>
                                <div class="template-content">Your name:
Your email:
Alternate email (optional; if the quote should be sent elsewhere):
Organization name:
Organization sector (Academic or Industry):
How many people need Premium access?:
Length of license (in years):
Name of institution, enterprise, lab, or team (optional; leave blank to use your organization name):
Names and emails of intended users (optional; leave blank to use your own email or it is a license just for yourself):
Admin name (optional; leave blank to use your name):
Admin email (optional; leave blank to use your email):
Billing name (optional):
Billing email (optional):
Billing address (optional):
Shipping address (optional):
VAT or Tax ID number (optional):</div>
                            </details>
                        </div>
                    </div>
                    
                    <button type="submit" id="submitBtn">
                        <span id="btnText">Run Automation</span>
                    </button>
                </form>
                
                {% if status %}
                <div class="alert {{ 'alert-success' if status_type == 'success' else 'alert-error' }}">
                    <span>{{ '✓' if status_type == 'success' else '✕' }}</span>
                    <span>{{ status }}</span>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <script>
    const form = document.getElementById('automationForm');
    const btn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    
    form.addEventListener('submit', function(e) {
        btn.disabled = true;
        btnText.innerHTML = '<span class="loading-dots"><span></span><span></span><span></span></span> Processing';
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
                return True, "Successfully submitted! Your form has been filled automatically."
            except Exception as e:
                print(f"Automation error: {str(e)}")
                return False, f"Something went wrong: {str(e)}"
        
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