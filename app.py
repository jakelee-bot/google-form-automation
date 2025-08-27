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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-primary: #0f0f0f;
            --bg-secondary: #1a1a1a;
            --bg-card: rgba(255, 255, 255, 0.02);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-primary: rgba(255, 255, 255, 0.95);
            --text-secondary: rgba(255, 255, 255, 0.6);
            --text-muted: rgba(255, 255, 255, 0.4);
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
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
            opacity: 0.5;
            animation: float 20s infinite ease-in-out;
        }
        
        .orb-1 {
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
            top: -200genuinepx;
            left: -200px;
            animation-delay: 0s;
        }
        
        .orb-2 {
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, #8b5cf6 0%, transparent 70%);
            bottom: -150px;
            right: -150px;
            animation-delay: 5s;
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
            gap: 12px;
        }
        
        .logo-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            color: white;
        }
        
        .logo-text {
            font-size: 24px;
            font-weight: 600;
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
                0 20px 25px -5px rgba(0, 0, 0, 0.3),
                0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
        
        .card-header {
            padding: 32px;
            border-bottom: 1px solid var(--border-color);
            background: rgba(255, 255, 255, 0.01);
        }
        
        .card-body {
            padding: 32px;
        }
        
        h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 15px;
        }
        
        /* Form elements */
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
            min-height: 280px;
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
            border-color: var(--accent);
            background: rgba(59, 130, 246, 0.05);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        textarea::placeholder {
            color: var(--text-muted);
        }
        
        /* Button */
        button {
            width: 100%;
            padding: 12px 24px;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        
        button:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        /* Status messages */
        .alert {
            margin-top: 24px;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            display: flex;
            align-items: center;
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
        
        .alert-icon {
            font-size: 20px;
        }
        
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Loading state */
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
        
        /* Info box */
        .info-box {
            margin-top: 16px;
            padding: 12px;
            background: rgba(59, 130, 246, 0.05);
            border: 1px solid rgba(59, 130, 246, 0.1);
            border-radius: 6px;
            font-size: 13px;
            color: var(--text-secondary);
        }
        
        @media (max-width: 640px) {
            .container {
                padding: 40px 16px;
            }
            
            .card-header, .card-body {
                padding: 24px 20px;
            }
        }
    </style>
</head>
<body>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    
    <div class="container">
        <div class="logo">
            <div class="logo-icon">FA</div>
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
How many people need Premium access? 5
Length of license: 2" 
                            required
                            spellcheck="false"
                        ></textarea>
                        
                        <div class="info-box">
                            💡 Pro tip: Use the exact format shown above for best results
                        </div>
                    </div>
                    
                    <button type="submit" id="submitBtn">
                        <span id="btnText">Run Automation</span>
                    </button>
                </form>
                
                {% if status %}
                <div class="alert {{ 'alert-success' if status_type == 'success' else 'alert-error' }}">
                    <span class="alert-icon">{{ '✓' if status_type == 'success' else '✕' }}</span>
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
        this.style.height = Math.min(this.scrollHeight, 400) + 'px';
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