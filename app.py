from flask import Flask, render_template_string, request, jsonify
import asyncio
import json
import os
from src.form_automation import GoogleFormBot
from src.parser_only import MessageParser

app = Flask(__name__, static_folder='static')

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
            max-width: 800px;
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
        
        h2 {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
            color: var(--text-primary);
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
        
        textarea, input[type="text"], input[type="email"], input[type="number"], select {
            width: 100%;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            color: var(--text-primary);
            transition: all 0.2s ease;
        }
        
        textarea {
            min-height: 200px;
            resize: vertical;
            font-family: 'SF Mono', Monaco, monospace;
        }
        
        input:focus, textarea:focus, select:focus {
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
        
        .button-secondary {
            background: rgba(255, 255, 255, 0.1);
            margin-right: 12px;
        }
        
        .button-secondary:hover {
            background: rgba(255, 255, 255, 0.15);
        }
        
        /* Two column layout */
        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        
        @media (max-width: 640px) {
            .form-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Results section */
        .extracted-data {
            background: rgba(0, 102, 255, 0.05);
            border: 1px solid rgba(0, 102, 255, 0.2);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 32px;
        }
        
        .data-field {
            margin-bottom: 20px;
        }
        
        .data-field:last-child {
            margin-bottom: 0;
        }
        
        .field-label {
            font-size: 12px;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 4px;
            letter-spacing: 0.05em;
        }
        
        .button-group {
            display: flex;
            gap: 12px;
            margin-top: 24px;
        }
        
        .button-group button {
            flex: 1;
        }
        
        /* Hidden sections */
        .hidden {
            display: none;
        }
        
        /* Loading state */
        .loading {
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: var(--biorender-blue);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Status messages */
        .alert {
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
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
    </style>
</head>
<body>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    
    <div class="container">
        <div class="logo">
    <div style="background: white; padding: 12px; border-radius: 12px; display: inline-block;">
        <img src="/static/images/biorender-logo.png" alt="BioRender" style="height: 40px; width: auto;">
    </div>
</div>
        
        <div class="card">
            <!-- Step 1: Input Email -->
            <div id="step1" class="step">
                <div class="card-header">
                    <h1>Extract Form Data from Email</h1>
                    <p class="subtitle">Paste your email and we'll extract the form information</p>
                </div>
                
                <div class="card-body">
                    <div class="form-group">
                        <label for="emailInput">Paste your email here</label>
                        <textarea 
                            id="emailInput" 
                            placeholder="Paste the entire email containing form details..."
                            rows="10"
                        ></textarea>
                    </div>
                    
                    <button onclick="parseEmail()">Extract Information</button>
                </div>
            </div>
            
            <!-- Step 2: Review and Edit -->
            <div id="step2" class="step hidden">
                <div class="card-header">
                    <h1>Review Extracted Information</h1>
                    <p class="subtitle">Verify and edit the extracted data before submitting</p>
                </div>
                
                <div class="card-body">
                    <form id="reviewForm">
                        <div class="extracted-data">
                            <h2>Contact Information</h2>
                            <div class="form-grid">
                                <div class="data-field">
                                    <div class="field-label">Your Name</div>
                                    <input type="text" id="name" name="name">
                                </div>
                                <div class="data-field">
                                    <div class="field-label">Your Email</div>
                                    <input type="email" id="email" name="email">
                                </div>
                            </div>
                            
                            <div class="data-field">
                                <div class="field-label">Alternate Email (optional)</div>
                                <input type="email" id="alternate_email" name="alternate_email">
                            </div>
                        </div>
                        
                        <div class="extracted-data">
                            <h2>Organization Details</h2>
                            <div class="form-grid">
                                <div class="data-field">
                                    <div class="field-label">Organization Name</div>
                                    <input type="text" id="organization_name" name="organization_name">
                                </div>
                                <div class="data-field">
                                    <div class="field-label">Organization Sector</div>
                                    <select id="organization_sector" name="organization_sector">
                                        <option value="Academic">Academic</option>
                                        <option value="Industry">Industry</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div class="form-grid">
                                <div class="data-field">
                                    <div class="field-label">Number of Premium Users</div>
                                    <input type="number" id="num_premium_users" name="num_premium_users" min="1">
                                </div>
                                <div class="data-field">
                                    <div class="field-label">License Length (years)</div>
                                    <input type="number" id="license_length_years" name="license_length_years" min="1">
                                </div>
                            </div>
                            
                            <div class="data-field">
                                <div class="field-label">Institution/Lab/Team Name (optional)</div>
                                <input type="text" id="institution_name" name="institution_name">
                            </div>
                        </div>
                        
                        <div class="extracted-data">
                            <h2>User Details</h2>
                            <div class="data-field">
                                <div class="field-label">Names and Emails of Intended Users (optional)</div>
                                <textarea id="user_names_emails" name="user_names_emails" rows="3"></textarea>
                            </div>
                            
                            <div class="form-grid">
                                <div class="data-field">
                                    <div class="field-label">Admin Name (optional)</div>
                                    <input type="text" id="admin_name" name="admin_name">
                                </div>
                                <div class="data-field">
                                    <div class="field-label">Admin Email (optional)</div>
                                    <input type="email" id="admin_email" name="admin_email">
                                </div>
                            </div>
                        </div>
                        
                        <div class="extracted-data">
                            <h2>Billing Information</h2>
                            <div class="form-grid">
                                <div class="data-field">
                                    <div class="field-label">Billing Name (optional)</div>
                                    <input type="text" id="billing_name" name="billing_name">
                                </div>
                                <div class="data-field">
                                    <div class="field-label">Billing Email (optional)</div>
                                    <input type="email" id="billing_email" name="billing_email">
                                </div>
                            </div>
                            
                            <div class="data-field">
                                <div class="field-label">Billing Address (optional)</div>
                                <textarea id="billing_address" name="billing_address" rows="3"></textarea>
                            </div>
                            
                            <div class="data-field">
                                <div class="field-label">Shipping Address (optional)</div>
                                <textarea id="shipping_address" name="shipping_address" rows="3"></textarea>
                            </div>
                            
                            <div class="data-field">
                                <div class="field-label">VAT or Tax ID Number (optional)</div>
                                <input type="text" id="vat_tax_id" name="vat_tax_id">
                            </div>
                        </div>
                        
                        <div class="button-group">
                            <button type="button" class="button-secondary" onclick="goBack()">Go Back</button>
                            <button type="submit">Submit to Form</button>
                        </div>
                    </form>
                </div>
            </div>
            
            <!-- Step 3: Processing -->
            <div id="step3" class="step hidden">
                <div class="card-body">
                    <div class="loading">
                        <div class="spinner"></div>
                        <p style="margin-top: 20px;">Processing your form submission...</p>
                    </div>
                </div>
            </div>
            
            <!-- Step 4: Result -->
            <div id="step4" class="step hidden">
                <div class="card-header">
                    <h1>Form Submission Complete</h1>
                </div>
                <div class="card-body">
                    <div id="resultMessage"></div>
                    <button onclick="startOver()" style="margin-top: 24px;">Submit Another Form</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
    function showStep(stepNumber) {
        document.querySelectorAll('.step').forEach(step => {
            step.classList.add('hidden');
        });
        document.getElementById('step' + stepNumber).classList.remove('hidden');
    }
    
    async function parseEmail() {
        const emailContent = document.getElementById('emailInput').value;
        
        if (!emailContent.trim()) {
            alert('Please paste an email to extract information from.');
            return;
        }
        
        // Show loading
        showStep(3);
        
        try {
            const response = await fetch('/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: emailContent })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Populate form fields with extracted data
                populateForm(data.data);
                showStep(2);
            } else {
                alert('Failed to parse email: ' + data.error);
                showStep(1);
            }
        } catch (error) {
            alert('Error: ' + error.message);
            showStep(1);
        }
    }
    
    function populateForm(data) {
        // Populate all form fields with extracted data
        for (const [key, value] of Object.entries(data)) {
            const field = document.getElementById(key);
            if (field) {
                field.value = value || '';
            }
        }
    }
    
    function goBack() {
        showStep(1);
    }
    
    function startOver() {
        document.getElementById('emailInput').value = '';
        document.getElementById('reviewForm').reset();
        showStep(1);
    }
    
    // Handle form submission
    document.getElementById('reviewForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Collect all form data
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        // Build the structured message
        const message = buildFormMessage(data);
        
        // Show processing
        showStep(3);
        
        try {
            const response = await fetch('/submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'message=' + encodeURIComponent(message)
            });
            
            const html = await response.text();
            
            // Extract success/error message from response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const alert = doc.querySelector('.alert');
            
            if (alert) {
                document.getElementById('resultMessage').innerHTML = alert.outerHTML;
            } else {
                document.getElementById('resultMessage').innerHTML = 
                    '<div class="alert alert-success">Form submitted successfully!</div>';
            }
            
            showStep(4);
        } catch (error) {
            document.getElementById('resultMessage').innerHTML = 
                '<div class="alert alert-error">Error: ' + error.message + '</div>';
            showStep(4);
        }
    });
    
    function buildFormMessage(data) {
        // Build structured message from form data
        const lines = [];
        
        if (data.name) lines.push('Your name: ' + data.name);
        if (data.email) lines.push('Your email: ' + data.email);
        if (data.alternate_email) lines.push('Alternate email: ' + data.alternate_email);
        if (data.organization_name) lines.push('Organization name: ' + data.organization_name);
        if (data.organization_sector) lines.push('Organization sector: ' + data.organization_sector);
        if (data.num_premium_users) lines.push('How many people need Premium access?: ' + data.num_premium_users);
        if (data.license_length_years) lines.push('Length of license (in years): ' + data.license_length_years);
        if (data.institution_name) lines.push('Name of institution: ' + data.institution_name);
        if (data.user_names_emails) lines.push('Names and emails of intended users: ' + data.user_names_emails);
        if (data.admin_name) lines.push('Admin name: ' + data.admin_name);
        if (data.admin_email) lines.push('Admin email: ' + data.admin_email);
        if (data.billing_name) lines.push('Billing name: ' + data.billing_name);
        if (data.billing_email) lines.push('Billing email: ' + data.billing_email);
        if (data.billing_address) lines.push('Billing address: ' + data.billing_address);
        if (data.shipping_address) lines.push('Shipping address: ' + data.shipping_address);
        if (data.vat_tax_id) lines.push('VAT or Tax ID number: ' + data.vat_tax_id);
        
        return lines.join('\n');
    }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/parse', methods=['POST'])
def parse():
    """Parse email content and extract form data"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        parser = MessageParser()
        extracted = parser.extract_data(message)
        
        return jsonify({
            'success': True,
            'data': {
                'name': extracted.name,
                'email': extracted.email,
                'alternate_email': extracted.alternate_email,
                'organization_name': extracted.organization_name,
                'organization_sector': extracted.organization_sector,
                'num_premium_users': extracted.num_premium_users,
                'license_length_years': extracted.license_length_years,
                'institution_name': extracted.institution_name,
                'admin_name': extracted.admin_name,
                'admin_email': extracted.admin_email,
                'billing_name': extracted.billing_name,
                'billing_email': extracted.billing_email,
                'billing_address': extracted.billing_address,
                'shipping_address': extracted.shipping_address,
                'vat_tax_id': extracted.vat_tax_id,
                'user_names_emails': extracted.user_names_emails
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/submit', methods=['POST'])
def submit():
    """Submit the reviewed data to the form"""
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