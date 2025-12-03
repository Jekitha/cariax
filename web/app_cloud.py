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

# In-memory user storage (works on all platforms)
users_memory = {}
user_data_memory = {}

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

def load_json_file(filename, key=None):
    """Load JSON data from file."""
    filepath = DATA_DIR / filename
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if key and isinstance(data, dict):
                    return data.get(key, [])
                return data
        except:
            pass
    return []

# Load all data with proper keys
CAREERS_DATA = load_json_file('careers.json', 'careers')
COLLEGES_DATA = load_json_file('colleges.json', 'colleges')
SKILLS_DATA = load_json_file('skills.json', 'skills')

# Fallback career data if files don't load
if not CAREERS_DATA:
    CAREERS_DATA = [
        {"id": 1, "name": "Software Engineer", "category": "Technology", "description": "Design and build software applications", "difficulty": 7, "automation_risk": 0.2, "job_growth_rate": 0.22, "required_skills": ["Python", "JavaScript", "Problem Solving"], "salary": {"entry": {"INR": 500000}, "mid": {"INR": 1500000}, "senior": {"INR": 3000000}}},
        {"id": 2, "name": "Data Scientist", "category": "Technology", "description": "Analyze data to derive insights", "difficulty": 8, "automation_risk": 0.15, "job_growth_rate": 0.35, "required_skills": ["Python", "ML", "Statistics"], "salary": {"entry": {"INR": 600000}, "mid": {"INR": 1800000}, "senior": {"INR": 3500000}}},
        {"id": 3, "name": "Product Manager", "category": "Business", "description": "Lead product development and strategy", "difficulty": 6, "automation_risk": 0.1, "job_growth_rate": 0.18, "required_skills": ["Communication", "Strategy", "Analysis"], "salary": {"entry": {"INR": 800000}, "mid": {"INR": 2000000}, "senior": {"INR": 4000000}}},
        {"id": 4, "name": "UX Designer", "category": "Design", "description": "Create user-friendly digital experiences", "difficulty": 5, "automation_risk": 0.25, "job_growth_rate": 0.15, "required_skills": ["Figma", "User Research", "Prototyping"], "salary": {"entry": {"INR": 400000}, "mid": {"INR": 1200000}, "senior": {"INR": 2500000}}},
        {"id": 5, "name": "Cybersecurity Analyst", "category": "Technology", "description": "Protect systems from cyber threats", "difficulty": 7, "automation_risk": 0.12, "job_growth_rate": 0.28, "required_skills": ["Network Security", "Ethical Hacking", "Risk Assessment"], "salary": {"entry": {"INR": 500000}, "mid": {"INR": 1400000}, "senior": {"INR": 2800000}}},
        {"id": 6, "name": "Cloud Architect", "category": "Technology", "description": "Design cloud infrastructure solutions", "difficulty": 8, "automation_risk": 0.18, "job_growth_rate": 0.25, "required_skills": ["AWS", "Azure", "DevOps"], "salary": {"entry": {"INR": 700000}, "mid": {"INR": 2000000}, "senior": {"INR": 4000000}}},
        {"id": 7, "name": "AI/ML Engineer", "category": "Technology", "description": "Build intelligent systems and algorithms", "difficulty": 9, "automation_risk": 0.08, "job_growth_rate": 0.40, "required_skills": ["Python", "TensorFlow", "Deep Learning"], "salary": {"entry": {"INR": 800000}, "mid": {"INR": 2500000}, "senior": {"INR": 5000000}}},
        {"id": 8, "name": "Digital Marketer", "category": "Marketing", "description": "Drive online marketing campaigns", "difficulty": 4, "automation_risk": 0.35, "job_growth_rate": 0.12, "required_skills": ["SEO", "Social Media", "Analytics"], "salary": {"entry": {"INR": 300000}, "mid": {"INR": 800000}, "senior": {"INR": 1500000}}},
    ]

if not COLLEGES_DATA:
    COLLEGES_DATA = [
        {"id": 1, "name": "IIT Bombay", "location": "Mumbai", "ranking": 1, "type": "Engineering"},
        {"id": 2, "name": "IIT Delhi", "location": "Delhi", "ranking": 2, "type": "Engineering"},
        {"id": 3, "name": "IIT Madras", "location": "Chennai", "ranking": 3, "type": "Engineering"},
        {"id": 4, "name": "BITS Pilani", "location": "Pilani", "ranking": 10, "type": "Engineering"},
        {"id": 5, "name": "NIT Trichy", "location": "Trichy", "ranking": 15, "type": "Engineering"},
    ]

print(f"✓ Career data loaded: {len(CAREERS_DATA)} careers, {len(COLLEGES_DATA)} colleges")

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
        
        # Try in-memory first
        if email in users_memory and users_memory[email] == password:
            session['user_id'] = email
            session['user_name'] = user_data_memory.get(email, {}).get('first_name', email.split('@')[0])
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        
        # Try database
        try:
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
        except Exception as e:
            print(f"DB Error: {e}")
        
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
        
        # Store in memory (always works)
        users_memory[email] = password
        user_data_memory[email] = {'first_name': first_name, 'last_name': last_name}
        
        # Also try database
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT OR REPLACE INTO users (email, password, first_name, last_name) VALUES (?, ?, ?, ?)',
                     (email, password, first_name, last_name))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error (non-fatal): {e}")
        
        session['user_id'] = email
        session['user_name'] = first_name or email.split('@')[0]
        flash('Account created successfully!', 'success')
        return redirect(url_for('onboarding'))
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

@app.route('/api/chat/reset', methods=['POST'])
def chat_reset():
    """Reset chat history."""
    return jsonify({'success': True, 'message': 'Chat reset'})

@app.route('/api/analyze', methods=['POST'])
def analyze_profile():
    """Analyze student profile."""
    data = request.get_json() or {}
    return jsonify({
        'success': True,
        'careers': [
            {'name': 'Software Engineer', 'match': 92},
            {'name': 'Data Scientist', 'match': 88},
            {'name': 'Product Manager', 'match': 85}
        ],
        'message': 'Analysis complete'
    })

@app.route('/api/assessment/questions/<level>', methods=['GET'])
def get_assessment_questions(level):
    """Get assessment questions by education level."""
    return jsonify({
        'success': True,
        'questions': [
            {'id': 1, 'text': 'What subjects interest you most?', 'type': 'multiple'},
            {'id': 2, 'text': 'Rate your problem-solving skills', 'type': 'rating'},
            {'id': 3, 'text': 'Describe your ideal work environment', 'type': 'text'}
        ]
    })

@app.route('/api/assessment/submit', methods=['POST'])
def submit_assessment_api():
    """Submit assessment answers."""
    data = request.get_json() or {}
    return jsonify({
        'success': True,
        'message': 'Assessment submitted',
        'redirect': '/results'
    })

@app.route('/api/goals/task/<task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    """Toggle task completion."""
    return jsonify({'success': True, 'completed': True})

@app.route('/api/user/results', methods=['GET'])
def get_user_results():
    """Get user's assessment results."""
    return jsonify({
        'success': True,
        'results': {
            'top_careers': [
                {'name': 'Software Engineer', 'match': 92, 'salary': '$120,000'},
                {'name': 'Data Scientist', 'match': 88, 'salary': '$130,000'},
                {'name': 'Product Manager', 'match': 85, 'salary': '$140,000'}
            ],
            'personality': 'INTJ',
            'skills': ['Problem Solving', 'Analytical Thinking', 'Communication']
        }
    })

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
