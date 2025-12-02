"""
Simple Flask App for Render Deployment
"""

import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
import secrets
from datetime import datetime

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Simple in-memory user storage for demo
users = {}
user_data = {}

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ============== Health Check ==============
@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

# ============== Auth Routes ==============
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if email in users and users[email] == password:
            session['user_id'] = email
            session['user_name'] = email.split('@')[0]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    return render_template('auth_login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        users[email] = password
        user_data[email] = {'first_name': first_name, 'last_name': last_name}
        session['user_id'] = email
        session['user_name'] = first_name or email.split('@')[0]
        flash('Account created!', 'success')
        return redirect(url_for('onboarding'))
    return render_template('auth_signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ============== Main Pages ==============
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/onboarding')
def onboarding():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('onboarding.html')

@app.route('/roadmap')
def roadmap():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('roadmap.html')

@app.route('/careers')
def careers():
    return render_template('careers.html')

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('results.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('profile.html')

@app.route('/scam-detector')
def scam_detector():
    return render_template('scam_detector.html')

@app.route('/behaviour-analysis')
def behaviour_analysis():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('behaviour_analysis.html')

@app.route('/job-market')
def job_market():
    return render_template('job_market.html')

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('chat.html')

@app.route('/colleges')
def colleges():
    return render_template('colleges.html')

# ============== API Endpoints ==============
@app.route('/api/submit-assessment', methods=['POST'])
def submit_assessment():
    return jsonify({'success': True, 'message': 'Assessment saved'})

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.get_json()
    message = data.get('message', '')
    return jsonify({
        'success': True,
        'response': f"Thanks for your message: {message}. This is a demo response."
    })

@app.route('/api/check-scam', methods=['POST'])
def check_scam():
    data = request.get_json()
    return jsonify({
        'success': True,
        'is_scam': False,
        'confidence': 0.1,
        'message': 'This appears to be a legitimate job posting.'
    })

@app.route('/api/analyze-behaviour', methods=['POST'])
def analyze_behaviour():
    data = request.get_json()
    return jsonify({
        'success': True,
        'feedback': 'Great answer! You demonstrated good communication skills.',
        'score': 85
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
