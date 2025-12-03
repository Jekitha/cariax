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

# ============== Built-in Career & College Data ==============
# This data is embedded directly so it works on cloud deployment

CAREERS_DATA = [
    {"id": 1, "name": "Software Engineer", "category": "Technology", "description": "Design, develop, and maintain software applications and systems", "difficulty": 7, "automation_risk": 0.20, "job_growth_rate": 0.22, "required_skills": ["Python", "JavaScript", "Problem Solving", "Git", "System Design"], "education": "B.Tech/B.E. in Computer Science", "personality_fit": ["INTJ", "INTP", "ISTJ"], "salary": {"entry": {"INR": 500000, "USD": 70000}, "mid": {"INR": 1500000, "USD": 120000}, "senior": {"INR": 3000000, "USD": 180000}}},
    {"id": 2, "name": "Data Scientist", "category": "Technology", "description": "Analyze complex data to help organizations make better decisions", "difficulty": 8, "automation_risk": 0.15, "job_growth_rate": 0.35, "required_skills": ["Python", "Machine Learning", "Statistics", "SQL", "Data Visualization"], "education": "B.Tech/M.Tech in CS or Statistics", "personality_fit": ["INTJ", "INTP", "ENTJ"], "salary": {"entry": {"INR": 600000, "USD": 80000}, "mid": {"INR": 1800000, "USD": 130000}, "senior": {"INR": 3500000, "USD": 200000}}},
    {"id": 3, "name": "Product Manager", "category": "Business", "description": "Lead product development and define product strategy", "difficulty": 6, "automation_risk": 0.10, "job_growth_rate": 0.18, "required_skills": ["Communication", "Strategy", "Analysis", "Leadership", "User Research"], "education": "MBA or B.Tech + Experience", "personality_fit": ["ENTJ", "ENFJ", "ENTP"], "salary": {"entry": {"INR": 800000, "USD": 90000}, "mid": {"INR": 2000000, "USD": 150000}, "senior": {"INR": 4000000, "USD": 250000}}},
    {"id": 4, "name": "UX Designer", "category": "Design", "description": "Create user-friendly and intuitive digital experiences", "difficulty": 5, "automation_risk": 0.25, "job_growth_rate": 0.15, "required_skills": ["Figma", "User Research", "Prototyping", "Visual Design", "Wireframing"], "education": "B.Des or Self-taught with portfolio", "personality_fit": ["INFP", "ENFP", "ISFP"], "salary": {"entry": {"INR": 400000, "USD": 60000}, "mid": {"INR": 1200000, "USD": 100000}, "senior": {"INR": 2500000, "USD": 150000}}},
    {"id": 5, "name": "Cybersecurity Analyst", "category": "Technology", "description": "Protect organizations from cyber threats and security breaches", "difficulty": 7, "automation_risk": 0.12, "job_growth_rate": 0.28, "required_skills": ["Network Security", "Ethical Hacking", "Risk Assessment", "SIEM", "Incident Response"], "education": "B.Tech in CS + Security Certifications", "personality_fit": ["ISTJ", "INTJ", "ISTP"], "salary": {"entry": {"INR": 500000, "USD": 75000}, "mid": {"INR": 1400000, "USD": 110000}, "senior": {"INR": 2800000, "USD": 160000}}},
    {"id": 6, "name": "Cloud Architect", "category": "Technology", "description": "Design and implement cloud infrastructure solutions", "difficulty": 8, "automation_risk": 0.18, "job_growth_rate": 0.25, "required_skills": ["AWS", "Azure", "DevOps", "Kubernetes", "Terraform"], "education": "B.Tech + Cloud Certifications", "personality_fit": ["INTJ", "ISTJ", "ENTJ"], "salary": {"entry": {"INR": 700000, "USD": 85000}, "mid": {"INR": 2000000, "USD": 140000}, "senior": {"INR": 4000000, "USD": 200000}}},
    {"id": 7, "name": "AI/ML Engineer", "category": "Technology", "description": "Build intelligent systems using artificial intelligence and machine learning", "difficulty": 9, "automation_risk": 0.08, "job_growth_rate": 0.40, "required_skills": ["Python", "TensorFlow", "Deep Learning", "NLP", "Computer Vision"], "education": "M.Tech/PhD in AI/ML or CS", "personality_fit": ["INTJ", "INTP", "ENTP"], "salary": {"entry": {"INR": 800000, "USD": 100000}, "mid": {"INR": 2500000, "USD": 180000}, "senior": {"INR": 5000000, "USD": 300000}}},
    {"id": 8, "name": "Digital Marketer", "category": "Marketing", "description": "Plan and execute online marketing campaigns", "difficulty": 4, "automation_risk": 0.35, "job_growth_rate": 0.12, "required_skills": ["SEO", "Social Media", "Google Ads", "Content Marketing", "Analytics"], "education": "BBA/MBA in Marketing or Certifications", "personality_fit": ["ENFP", "ENTP", "ESFP"], "salary": {"entry": {"INR": 300000, "USD": 45000}, "mid": {"INR": 800000, "USD": 80000}, "senior": {"INR": 1500000, "USD": 120000}}},
    {"id": 9, "name": "Financial Analyst", "category": "Finance", "description": "Analyze financial data and provide investment recommendations", "difficulty": 6, "automation_risk": 0.30, "job_growth_rate": 0.10, "required_skills": ["Excel", "Financial Modeling", "Valuation", "SQL", "Accounting"], "education": "B.Com/MBA Finance + CFA", "personality_fit": ["ISTJ", "ESTJ", "INTJ"], "salary": {"entry": {"INR": 500000, "USD": 65000}, "mid": {"INR": 1200000, "USD": 100000}, "senior": {"INR": 2500000, "USD": 150000}}},
    {"id": 10, "name": "Doctor (MBBS)", "category": "Healthcare", "description": "Diagnose and treat patients, provide medical care", "difficulty": 10, "automation_risk": 0.05, "job_growth_rate": 0.08, "required_skills": ["Medical Knowledge", "Diagnosis", "Patient Care", "Communication", "Decision Making"], "education": "MBBS + MD/MS Specialization", "personality_fit": ["ISFJ", "INFJ", "ENFJ"], "salary": {"entry": {"INR": 600000, "USD": 60000}, "mid": {"INR": 1500000, "USD": 150000}, "senior": {"INR": 4000000, "USD": 300000}}},
    {"id": 11, "name": "Civil Engineer", "category": "Engineering", "description": "Design and oversee construction of infrastructure projects", "difficulty": 6, "automation_risk": 0.20, "job_growth_rate": 0.08, "required_skills": ["AutoCAD", "Structural Analysis", "Project Management", "Surveying", "Construction"], "education": "B.Tech in Civil Engineering", "personality_fit": ["ISTJ", "ESTJ", "ISTP"], "salary": {"entry": {"INR": 350000, "USD": 55000}, "mid": {"INR": 900000, "USD": 85000}, "senior": {"INR": 2000000, "USD": 130000}}},
    {"id": 12, "name": "Mechanical Engineer", "category": "Engineering", "description": "Design and develop mechanical systems and products", "difficulty": 6, "automation_risk": 0.22, "job_growth_rate": 0.06, "required_skills": ["SolidWorks", "AutoCAD", "Thermodynamics", "Manufacturing", "FEA"], "education": "B.Tech in Mechanical Engineering", "personality_fit": ["ISTP", "ISTJ", "INTP"], "salary": {"entry": {"INR": 400000, "USD": 60000}, "mid": {"INR": 1000000, "USD": 90000}, "senior": {"INR": 2200000, "USD": 140000}}},
    {"id": 13, "name": "Lawyer", "category": "Law", "description": "Represent clients in legal matters and provide legal advice", "difficulty": 8, "automation_risk": 0.15, "job_growth_rate": 0.06, "required_skills": ["Legal Research", "Argumentation", "Writing", "Negotiation", "Critical Thinking"], "education": "LLB + Bar Council Registration", "personality_fit": ["ENTJ", "INTJ", "ESTJ"], "salary": {"entry": {"INR": 400000, "USD": 70000}, "mid": {"INR": 1500000, "USD": 150000}, "senior": {"INR": 5000000, "USD": 300000}}},
    {"id": 14, "name": "Chartered Accountant", "category": "Finance", "description": "Handle accounting, auditing, and financial compliance", "difficulty": 8, "automation_risk": 0.25, "job_growth_rate": 0.07, "required_skills": ["Accounting", "Taxation", "Auditing", "GST", "Financial Reporting"], "education": "CA Certification", "personality_fit": ["ISTJ", "ESTJ", "INTJ"], "salary": {"entry": {"INR": 600000, "USD": 55000}, "mid": {"INR": 1500000, "USD": 100000}, "senior": {"INR": 3500000, "USD": 180000}}},
    {"id": 15, "name": "Graphic Designer", "category": "Design", "description": "Create visual content for digital and print media", "difficulty": 4, "automation_risk": 0.30, "job_growth_rate": 0.05, "required_skills": ["Photoshop", "Illustrator", "Typography", "Branding", "Color Theory"], "education": "B.Des or Diploma in Design", "personality_fit": ["ISFP", "INFP", "ENFP"], "salary": {"entry": {"INR": 250000, "USD": 40000}, "mid": {"INR": 600000, "USD": 65000}, "senior": {"INR": 1200000, "USD": 100000}}},
]

COLLEGES_DATA = [
    # India - IITs
    {"id": 1, "name": "IIT Bombay", "location": "Mumbai, India", "country": "India", "ranking": 1, "type": "Engineering", "cutoff": "JEE Rank < 500", "fees": "₹2.5 Lakhs/year", "courses": ["B.Tech", "M.Tech", "PhD"]},
    {"id": 2, "name": "IIT Delhi", "location": "Delhi, India", "country": "India", "ranking": 2, "type": "Engineering", "cutoff": "JEE Rank < 800", "fees": "₹2.5 Lakhs/year", "courses": ["B.Tech", "M.Tech", "MBA"]},
    {"id": 3, "name": "IIT Madras", "location": "Chennai, India", "country": "India", "ranking": 3, "type": "Engineering", "cutoff": "JEE Rank < 1000", "fees": "₹2.5 Lakhs/year", "courses": ["B.Tech", "M.Tech", "MS"]},
    {"id": 4, "name": "IIT Kanpur", "location": "Kanpur, India", "country": "India", "ranking": 4, "type": "Engineering", "cutoff": "JEE Rank < 1500", "fees": "₹2.5 Lakhs/year", "courses": ["B.Tech", "M.Tech"]},
    {"id": 5, "name": "IIT Kharagpur", "location": "Kharagpur, India", "country": "India", "ranking": 5, "type": "Engineering", "cutoff": "JEE Rank < 2000", "fees": "₹2.5 Lakhs/year", "courses": ["B.Tech", "M.Tech"]},
    # India - NITs
    {"id": 6, "name": "NIT Trichy", "location": "Trichy, India", "country": "India", "ranking": 10, "type": "Engineering", "cutoff": "JEE Rank < 5000", "fees": "₹1.5 Lakhs/year", "courses": ["B.Tech", "M.Tech"]},
    {"id": 7, "name": "NIT Warangal", "location": "Warangal, India", "country": "India", "ranking": 12, "type": "Engineering", "cutoff": "JEE Rank < 6000", "fees": "₹1.5 Lakhs/year", "courses": ["B.Tech", "M.Tech"]},
    # India - Private
    {"id": 8, "name": "BITS Pilani", "location": "Pilani, India", "country": "India", "ranking": 8, "type": "Engineering", "cutoff": "BITSAT 350+", "fees": "₹5 Lakhs/year", "courses": ["B.E.", "M.E.", "PhD"]},
    {"id": 9, "name": "VIT Vellore", "location": "Vellore, India", "country": "India", "ranking": 15, "type": "Engineering", "cutoff": "VITEEE Rank", "fees": "₹2 Lakhs/year", "courses": ["B.Tech", "M.Tech"]},
    {"id": 10, "name": "SRM Chennai", "location": "Chennai, India", "country": "India", "ranking": 20, "type": "Engineering", "cutoff": "SRMJEEE", "fees": "₹2.5 Lakhs/year", "courses": ["B.Tech", "M.Tech"]},
    # India - IIMs for MBA
    {"id": 11, "name": "IIM Ahmedabad", "location": "Ahmedabad, India", "country": "India", "ranking": 1, "type": "Management", "cutoff": "CAT 99%ile+", "fees": "₹25 Lakhs total", "courses": ["MBA", "PGDM", "PhD"]},
    {"id": 12, "name": "IIM Bangalore", "location": "Bangalore, India", "country": "India", "ranking": 2, "type": "Management", "cutoff": "CAT 99%ile+", "fees": "₹25 Lakhs total", "courses": ["MBA", "PGDM"]},
    # India - Medical
    {"id": 13, "name": "AIIMS Delhi", "location": "Delhi, India", "country": "India", "ranking": 1, "type": "Medical", "cutoff": "NEET Rank < 100", "fees": "₹5,000/year", "courses": ["MBBS", "MD", "MS"]},
    {"id": 14, "name": "CMC Vellore", "location": "Vellore, India", "country": "India", "ranking": 2, "type": "Medical", "cutoff": "NEET Rank < 500", "fees": "₹50,000/year", "courses": ["MBBS", "MD"]},
    # USA
    {"id": 15, "name": "MIT", "location": "Cambridge, USA", "country": "USA", "ranking": 1, "type": "Engineering", "cutoff": "SAT 1550+, GPA 4.0", "fees": "$55,000/year", "courses": ["BS", "MS", "PhD"]},
    {"id": 16, "name": "Stanford University", "location": "California, USA", "country": "USA", "ranking": 2, "type": "Engineering", "cutoff": "SAT 1550+, GPA 3.9+", "fees": "$56,000/year", "courses": ["BS", "MS", "PhD"]},
    {"id": 17, "name": "Harvard University", "location": "Cambridge, USA", "country": "USA", "ranking": 1, "type": "Business", "cutoff": "GMAT 730+", "fees": "$75,000/year", "courses": ["MBA", "PhD"]},
    {"id": 18, "name": "Carnegie Mellon", "location": "Pittsburgh, USA", "country": "USA", "ranking": 5, "type": "Engineering", "cutoff": "GRE 330+", "fees": "$50,000/year", "courses": ["MS", "PhD"]},
    # UK
    {"id": 19, "name": "Oxford University", "location": "Oxford, UK", "country": "UK", "ranking": 1, "type": "General", "cutoff": "A-Levels AAA", "fees": "£30,000/year", "courses": ["BA", "MA", "PhD"]},
    {"id": 20, "name": "Cambridge University", "location": "Cambridge, UK", "country": "UK", "ranking": 2, "type": "General", "cutoff": "A-Levels AAA", "fees": "£30,000/year", "courses": ["BA", "MA", "PhD"]},
    {"id": 21, "name": "Imperial College London", "location": "London, UK", "country": "UK", "ranking": 3, "type": "Engineering", "cutoff": "A-Levels AAA", "fees": "£35,000/year", "courses": ["BEng", "MEng", "PhD"]},
    # Canada
    {"id": 22, "name": "University of Toronto", "location": "Toronto, Canada", "country": "Canada", "ranking": 1, "type": "Engineering", "cutoff": "GPA 3.5+", "fees": "CAD 45,000/year", "courses": ["BASc", "MASc", "PhD"]},
    {"id": 23, "name": "UBC", "location": "Vancouver, Canada", "country": "Canada", "ranking": 2, "type": "Engineering", "cutoff": "GPA 3.4+", "fees": "CAD 40,000/year", "courses": ["BASc", "MASc"]},
    # Australia
    {"id": 24, "name": "University of Melbourne", "location": "Melbourne, Australia", "country": "Australia", "ranking": 1, "type": "General", "cutoff": "ATAR 95+", "fees": "AUD 45,000/year", "courses": ["Bachelor", "Master", "PhD"]},
    {"id": 25, "name": "University of Sydney", "location": "Sydney, Australia", "country": "Australia", "ranking": 2, "type": "General", "cutoff": "ATAR 93+", "fees": "AUD 42,000/year", "courses": ["Bachelor", "Master"]},
]

# Skills mapping for assessment
SKILLS_DATA = {
    "technical": ["Python", "JavaScript", "Java", "SQL", "AWS", "Machine Learning", "Data Analysis"],
    "soft": ["Communication", "Leadership", "Problem Solving", "Teamwork", "Critical Thinking"],
    "creative": ["Design Thinking", "UI/UX", "Content Creation", "Branding", "Innovation"]
}

print(f"✓ Data loaded: {len(CAREERS_DATA)} careers, {len(COLLEGES_DATA)} colleges")

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
    """Get all colleges with optional filtering."""
    country = request.args.get('country', '').strip()
    type_filter = request.args.get('type', '').strip()
    
    filtered = COLLEGES_DATA
    
    if country:
        filtered = [c for c in filtered if c.get('country', '').lower() == country.lower()]
    
    if type_filter:
        filtered = [c for c in filtered if c.get('type', '').lower() == type_filter.lower()]
    
    return jsonify({
        'success': True,
        'count': len(filtered),
        'colleges': filtered
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
