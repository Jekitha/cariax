"""
CARIAX - AI Career Guidance System
Standalone Flask App for Cloud Deployment
"""

import os
import sys
import json
import secrets
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from datetime import datetime
import sqlite3

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Database path - use /tmp for cloud deployment
if os.environ.get('RENDER') or os.environ.get('RAILWAY'):
    DB_PATH = '/tmp/users.db'
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'users.db')

# ============== Database Functions ==============
def init_database():
    """Initialize the SQLite database."""
    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    except:
        pass
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  first_name TEXT,
                  last_name TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS assessments
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  data TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully!")

# Initialize database on startup
init_database()

# ============== Load Career Data ==============
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'

def load_json_file(filename):
    """Load JSON data from file."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Load all data
CAREERS_DATA = load_json_file('careers.json')
COLLEGES_DATA = load_json_file('colleges.json')
SKILLS_DATA = load_json_file('skills.json')

print("✓ Career data loaded successfully!")

# ============== Authentication Helpers ==============
def login_required(f):
    """Decorator to require login for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ============== Page Routes ==============
@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Login page."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, first_name FROM users WHERE email = ? AND password = ?', (email, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1] or email.split('@')[0]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('auth_login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    """Signup page."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (email, password, first_name, last_name) VALUES (?, ?, ?, ?)',
                     (email, password, first_name, last_name))
            conn.commit()
            user_id = c.lastrowid
            conn.close()
            
            session['user_id'] = user_id
            session['user_name'] = first_name or email.split('@')[0]
            flash('Account created successfully!', 'success')
            return redirect(url_for('onboarding'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Email already exists.', 'error')
    return render_template('auth_signup.html')

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    return render_template('dashboard.html')

@app.route('/onboarding')
@login_required
def onboarding():
    """Onboarding page."""
    return render_template('onboarding.html')

@app.route('/assessment')
@login_required
def assessment():
    """Career assessment page."""
    return render_template('assessment.html')

@app.route('/results')
@login_required
def results():
    """Results page."""
    return render_template('results.html')

@app.route('/roadmap')
@login_required
def roadmap():
    """Career roadmap page."""
    return render_template('roadmap.html')

@app.route('/careers')
def careers():
    """Career explorer page."""
    return render_template('careers.html')

@app.route('/chat')
@login_required
def chat():
    """AI Mentor chat page."""
    return render_template('chat.html')

@app.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('profile.html')

@app.route('/scam-detector')
def scam_detector():
    """Job scam detector page."""
    return render_template('scam_detector.html')

@app.route('/behaviour-analysis')
@login_required
def behaviour_analysis():
    """Interview behaviour analysis page."""
    return render_template('behaviour_analysis.html')

@app.route('/job-market')
def job_market():
    """Job market trends page."""
    return render_template('job_market.html')

@app.route('/colleges')
def colleges():
    """College finder page."""
    return render_template('colleges.html')

# ============== API Routes ==============
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/api/careers', methods=['GET'])
def get_careers():
    """Get all careers."""
    return jsonify({
        'success': True,
        'count': len(CAREERS_DATA),
        'careers': CAREERS_DATA
    })

@app.route('/api/careers/<career_name>', methods=['GET'])
def get_career_details(career_name):
    """Get career details."""
    for career in CAREERS_DATA:
        if career.get('name', '').lower() == career_name.lower():
            return jsonify({'success': True, 'data': career})
    return jsonify({'success': False, 'error': 'Career not found'}), 404

@app.route('/api/colleges', methods=['GET'])
def get_colleges():
    """Get all colleges."""
    return jsonify({
        'success': True,
        'count': len(COLLEGES_DATA),
        'colleges': COLLEGES_DATA
    })

@app.route('/api/submit-assessment', methods=['POST'])
def submit_assessment():
    """Submit career assessment."""
    data = request.get_json()
    
    if 'user_id' in session:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO assessments (user_id, data) VALUES (?, ?)',
                 (session['user_id'], json.dumps(data)))
        conn.commit()
        conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Assessment submitted successfully'
    })

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """AI Chat endpoint."""
    data = request.get_json()
    message = data.get('message', '')
    
    # Simple response generation
    responses = {
        'hello': "Hello! I'm your AI Career Mentor. How can I help you today?",
        'career': "I'd be happy to help you explore career options. What field interests you?",
        'job': "Finding the right job is important. What skills do you have?",
        'help': "I can help you with career guidance, skill assessment, and job market insights. What would you like to know?",
    }
    
    response = "I understand you're asking about career guidance. Could you please be more specific about what you'd like to know?"
    for key, val in responses.items():
        if key in message.lower():
            response = val
            break
    
    return jsonify({
        'success': True,
        'response': response
    })

@app.route('/api/check-scam', methods=['POST'])
def check_scam():
    """Check if job posting is a scam."""
    data = request.get_json()
    text = data.get('text', '').lower()
    
    # Scam detection keywords
    scam_keywords = ['guaranteed income', 'no experience needed', 'work from home $', 
                    'make money fast', 'mlm', 'pyramid', 'investment required',
                    'pay to start', 'unlimited earnings', 'be your own boss']
    
    scam_score = sum(1 for kw in scam_keywords if kw in text)
    is_scam = scam_score >= 2
    confidence = min(scam_score * 0.2, 0.95) if is_scam else max(0.1, 0.5 - scam_score * 0.1)
    
    return jsonify({
        'success': True,
        'is_scam': is_scam,
        'confidence': confidence,
        'message': 'This appears to be a scam job posting. Be careful!' if is_scam else 'This appears to be a legitimate job posting.',
        'red_flags': scam_score
    })

@app.route('/api/analyze-behaviour', methods=['POST'])
def analyze_behaviour():
    """Analyze interview behaviour."""
    data = request.get_json()
    answer = data.get('answer', '')
    question = data.get('question', '')
    
    # Simple analysis
    word_count = len(answer.split())
    has_examples = any(word in answer.lower() for word in ['example', 'instance', 'when i', 'i did', 'i was'])
    is_structured = any(word in answer.lower() for word in ['first', 'second', 'then', 'finally', 'because'])
    
    score = 50
    feedback_points = []
    
    if word_count < 20:
        feedback_points.append("Try to provide more detailed answers.")
    elif word_count > 50:
        score += 15
        feedback_points.append("Good detail in your response!")
    
    if has_examples:
        score += 20
        feedback_points.append("Great use of examples to illustrate your point.")
    else:
        feedback_points.append("Consider adding specific examples to strengthen your answer.")
    
    if is_structured:
        score += 15
        feedback_points.append("Well-structured response.")
    else:
        feedback_points.append("Try using transition words to organize your thoughts.")
    
    score = min(score, 100)
    
    return jsonify({
        'success': True,
        'score': score,
        'feedback': ' '.join(feedback_points),
        'word_count': word_count,
        'has_examples': has_examples,
        'is_structured': is_structured
    })

@app.route('/api/job-market', methods=['GET'])
def job_market_api():
    """Get job market data."""
    # Sample job market data
    job_data = {
        'trending_jobs': [
            {'title': 'AI/ML Engineer', 'growth': 35, 'demand': 'High'},
            {'title': 'Data Scientist', 'growth': 28, 'demand': 'High'},
            {'title': 'Cloud Architect', 'growth': 25, 'demand': 'High'},
            {'title': 'Cybersecurity Analyst', 'growth': 22, 'demand': 'High'},
            {'title': 'Full Stack Developer', 'growth': 20, 'demand': 'Medium-High'},
        ],
        'industry_growth': {
            'Technology': 15,
            'Healthcare': 12,
            'Finance': 8,
            'E-commerce': 18,
            'Education': 6
        }
    }
    return jsonify({'success': True, 'data': job_data})

# ============== Error Handlers ==============
@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============== Main ==============
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("    CARIAX - AI Career Guidance System")
    print("=" * 60)
    print(f"    Server: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
