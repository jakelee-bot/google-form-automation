from flask import Flask, render_template_string, request, jsonify
import asyncio
import json
from src.form_automation import GoogleFormBot, MessageParser

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Google Form Automation</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        textarea { width: 100%; height: 300px; }
        button { background: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .status { margin-top: 20px; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>Google Form Automation</h1>
    <form method="POST" action="/submit">
        <textarea name="message" placeholder="Paste your message here..."></textarea>
        <br><br>
        <button type="submit">Fill Form</button>
    </form>
    {% if status %}
    <div class="status {{ status_type }}">{{ status }}</div>
    {% endif %}
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/submit', methods=['POST'])
def submit():
    message = request.form.get('message', '')
    
    async def run_automation():
        bot = GoogleFormBot(headless=True, page_by_page=False)
        try:
            await bot.setup()
            await bot.run_automation(message)
            await bot.cleanup()
            return True, "Form submitted successfully!"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success, status = loop.run_until_complete(run_automation())
    
    return render_template_string(
        HTML_TEMPLATE, 
        status=status,
        status_type='success' if success else 'error'
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)