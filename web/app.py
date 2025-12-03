"""
Flask Web Application for AI Career Guidance System
Provides REST API and web interface for the career guidance platform.
"""

import os
import sys
import json
import asyncio
import secrets
from pathlib import Path
from functools import wraps
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_cors import CORS
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
except ImportError:
    pass  # dotenv not installed, will use environment variables directly

from main import CareerGuidanceSystem
from utils.data_processor import StudentProfile
from chatbot.mentor_chatbot import create_chatbot, SimpleChatbot
from auth.models import User, Session as UserSession, AssessmentResult, init_database

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Initialize the authentication database
init_database()

# OAuth Configuration (set these in environment variables for production)
OAUTH_CONFIG = {
    'google': {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID', ''),
        'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET', ''),
        'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/auth/google/callback'),
        'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'scope': 'email profile'
    },
    'github': {
        'client_id': os.environ.get('GITHUB_CLIENT_ID', ''),
        'client_secret': os.environ.get('GITHUB_CLIENT_SECRET', ''),
        'redirect_uri': os.environ.get('GITHUB_REDIRECT_URI', 'http://localhost:5000/auth/github/callback'),
        'auth_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'userinfo_url': 'https://api.github.com/user',
        'scope': 'user:email'
    }
}


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


def get_current_user():
    """Get the current logged-in user."""
    if 'user_id' in session:
        return User.get_by_id(session['user_id'])
    return None

# Context processor to add datetime to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now}

# Initialize the career guidance system
career_system = CareerGuidanceSystem(data_dir=str(PROJECT_ROOT / 'data'))

# Initialize chatbot (will use simple chatbot if no API key)
chatbot = create_chatbot(use_ai=True)


# ============== API Routes ==============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'oauth_configured': {
            'google': bool(OAUTH_CONFIG['google']['client_id']),
            'github': bool(OAUTH_CONFIG['github']['client_id'])
        }
    })


@app.route('/api/careers', methods=['GET'])
def get_careers():
    """Get all available careers."""
    careers = career_system.get_all_careers()
    return jsonify({
        'success': True,
        'count': len(careers),
        'careers': careers
    })


@app.route('/api/careers/<career_name>', methods=['GET'])
def get_career_details(career_name: str):
    """Get detailed information about a specific career."""
    details = career_system.get_career_details(career_name)
    if details:
        return jsonify({
            'success': True,
            'data': details
        })
    return jsonify({
        'success': False,
        'error': f'Career not found: {career_name}'
    }), 404


@app.route('/api/careers/compare', methods=['POST'])
def compare_careers():
    """Compare multiple careers."""
    data = request.json
    career_names = data.get('careers', [])
    
    if not career_names or len(career_names) < 2:
        return jsonify({
            'success': False,
            'error': 'At least 2 career names required'
        }), 400
    
    comparisons = career_system.compare_careers(career_names)
    return jsonify({
        'success': True,
        'comparisons': comparisons
    })


@app.route('/api/personality/questions', methods=['GET'])
def get_personality_questions():
    """Get personality test questions."""
    questions = career_system.get_personality_test()
    return jsonify({
        'success': True,
        'count': len(questions),
        'questions': questions
    })


@app.route('/api/personality/mbti/<mbti_type>', methods=['GET'])
def get_mbti_info(mbti_type: str):
    """Get information about an MBTI type."""
    mbti_type = mbti_type.upper()
    info = career_system.get_mbti_info(mbti_type)
    if info:
        return jsonify({
            'success': True,
            'mbti_type': mbti_type,
            'data': info
        })
    return jsonify({
        'success': False,
        'error': f'Invalid MBTI type: {mbti_type}'
    }), 400


@app.route('/api/analyze', methods=['POST'])
def analyze_student():
    """
    Analyze a student profile and generate career recommendations.
    
    Expected JSON body:
    {
        "name": "Student Name",
        "age": 17,
        "grade": "12th",
        "marks_10th": {"mathematics": 85, "science": 88, ...},
        "marks_12th": {"mathematics": 82, "physics": 85, ...},
        "subject_preferences": ["Computer Science", "Mathematics"],
        "interests": ["Technology", "Programming"],
        "skill_self_ratings": {"programming": 8, "mathematics": 7},
        "personality_answers": [...],
        "family_budget": 500000,
        "budget_currency": "INR",
        "preferred_locations": ["India", "USA"]
    }
    """
    try:
        data = request.json
        
        # Create student profile
        profile = StudentProfile(
            name=data.get('name', 'Student'),
            age=data.get('age', 18),
            grade=data.get('grade', '12th'),
            marks_10th=data.get('marks_10th', {}),
            marks_12th=data.get('marks_12th', {}),
            subject_preferences=data.get('subject_preferences', []),
            interests=data.get('interests', []),
            skill_self_ratings=data.get('skill_self_ratings', {}),
            personality_answers=data.get('personality_answers', []),
            family_budget=data.get('family_budget', 0),
            budget_currency=data.get('budget_currency', 'INR'),
            preferred_locations=data.get('preferred_locations', []),
            willing_to_relocate=data.get('willing_to_relocate', True)
        )
        
        # Analyze student
        report = career_system.analyze_student(profile)
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scam-check', methods=['POST'])
def check_scam():
    """
    Check content for potential scam indicators.
    
    Expected JSON body:
    {
        "text": "Content to analyze",
        "source": "optional source URL"
    }
    """
    data = request.json
    text = data.get('text', '')
    source = data.get('source', '')
    
    if not text:
        return jsonify({
            'success': False,
            'error': 'Text content is required'
        }), 400
    
    result = career_system.check_scam_content(text, source)
    return jsonify({
        'success': True,
        'result': result
    })


@app.route('/api/chat', methods=['POST'])
def chat_with_mentor():
    """
    Chat with the AI career mentor.
    
    Expected JSON body:
    {
        "message": "User's message"
    }
    """
    data = request.json
    message = data.get('message', '')
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'Message is required'
        }), 400
    
    try:
        # Use simple chatbot for sync response
        if isinstance(chatbot, SimpleChatbot):
            response = chatbot.chat(message)
        else:
            # For AI chatbot, run async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(chatbot.chat(message))
            finally:
                loop.close()
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chat/reset', methods=['POST'])
def reset_chat():
    """Reset the chat conversation."""
    chatbot.reset_conversation()
    return jsonify({
        'success': True,
        'message': 'Conversation reset successfully'
    })


@app.route('/api/colleges', methods=['POST'])
def find_colleges():
    """
    Find colleges for a career path.
    
    Expected JSON body:
    {
        "career_name": "Data Scientist",
        "budget": 500000,
        "budget_currency": "INR",
        "preferred_locations": ["India"]
    }
    """
    data = request.json
    
    career_name = data.get('career_name', '')
    budget = data.get('budget', 1000000)
    budget_currency = data.get('budget_currency', 'INR')
    preferred_locations = data.get('preferred_locations', [])
    
    if not career_name:
        return jsonify({
            'success': False,
            'error': 'Career name is required'
        }), 400
    
    colleges = career_system.college_finder.find_colleges(
        career_name=career_name,
        budget=budget,
        budget_currency=budget_currency,
        preferred_locations=preferred_locations
    )
    
    return jsonify({
        'success': True,
        'count': len(colleges),
        'colleges': colleges
    })


# ============== Web Routes ==============

@app.route('/')
def index():
    """Main page - redirects to login if not authenticated."""
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    """Main dashboard after login."""
    user = get_current_user()
    
    # If no session user, check for token in query params (for Simple Browser compatibility)
    if not user:
        token = request.args.get('token')
        if token:
            user_session = UserSession.get_by_token(token)
            if user_session:
                user = User.get_by_id(user_session['user_id'])
                if user:
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['user_email'] = user.email
    
    # Daily rotating job market insight for dashboard preview
    day_of_year = datetime.now().timetuple().tm_yday
    daily_insights = [
        "AI Hiring Surge - Top tech companies increased AI hiring by 40%",
        "Cloud Demand Peak - AWS and Azure certifications see 35% more job postings",
        "Cybersecurity Alert - 500K+ unfilled positions in India",
        "Data Science Boom - Companies investing heavily in data analytics",
        "DevOps Evolution - GitOps and Platform Engineering emerging as hot fields",
        "Startup Funding Up - Indian startups raised $2B+ this month",
        "Remote Jobs Growing - 67% of tech companies now offer remote options",
    ]
    market_insight = daily_insights[day_of_year % len(daily_insights)]
    
    # Render dashboard even without session - will use localStorage data on client
    if not user:
        # Create a guest view that JavaScript will populate from localStorage
        return render_template('dashboard.html',
            user=None,
            profile_complete=False,
            assessment_complete=False,
            progress=0,
            current_goal=None,
            careers_matched=0,
            goals_completed=0,
            streak_days=1,
            market_insight=market_insight
        )
    
    # Get user stats
    results = AssessmentResult.get_user_results(user.id) if user else []
    latest_result = results[0] if results else None
    
    return render_template('dashboard.html',
        user=user,
        profile_complete=bool(results),
        assessment_complete=bool(results),
        progress=25 if not results else 75,
        current_goal=None,
        careers_matched=len(latest_result.get('career_recommendations', [])) if latest_result else 0,
        goals_completed=0,
        streak_days=1,
        market_insight=market_insight
    )


@app.route('/onboarding')
def onboarding():
    """New comprehensive onboarding assessment."""
    user = get_current_user()
    return render_template('onboarding.html', user=user)


@app.route('/assessment')
def assessment():
    """Assessment page - redirect to onboarding."""
    return redirect(url_for('onboarding'))


@app.route('/careers')
def careers_page():
    """Careers exploration page."""
    return render_template('careers.html')


@app.route('/results')
def results_page():
    """Career results page with salary predictions."""
    user = get_current_user()
    return render_template('career_results.html', user=user)


@app.route('/roadmap')
def roadmap_page():
    """Interactive career roadmap with goal tracking."""
    user = get_current_user()
    return render_template('roadmap.html', user=user)


@app.route('/colleges')
def colleges_page():
    """College finder page for students."""
    user = get_current_user()
    return render_template('colleges.html', user=user)


@app.route('/job-market')
def job_market_page():
    """Job market forecast page with daily updated insights."""
    user = get_current_user()
    
    # Daily rotating job market insights - changes based on day of year
    day_of_year = datetime.now().timetuple().tm_yday
    
    # Daily tips that rotate
    daily_tips = [
        {"icon": "lightbulb", "title": "Learn AI Tools", "desc": "Companies are actively seeking professionals who can leverage AI tools like ChatGPT, GitHub Copilot for productivity."},
        {"icon": "certificate", "title": "Get Certified", "desc": "Cloud certifications (AWS, Azure) and specialized AI/ML certifications can boost your salary by 20-30%."},
        {"icon": "code-branch", "title": "Build Portfolio", "desc": "Open source contributions and personal projects on GitHub are valued more than certifications by many companies."},
        {"icon": "users", "title": "Network Actively", "desc": "80% of jobs are filled through networking. Attend tech meetups, connect on LinkedIn, and join developer communities."},
        {"icon": "brain", "title": "Focus on Soft Skills", "desc": "Communication, leadership, and problem-solving are increasingly valued alongside technical skills."},
        {"icon": "rocket", "title": "Consider Startups", "desc": "Early-stage startups offer faster growth opportunities, equity stakes, and diverse skill development."},
        {"icon": "laptop-code", "title": "Master Remote Work", "desc": "Remote work skills are essential. Learn async communication, time management, and virtual collaboration tools."},
    ]
    
    # Daily market insights that rotate
    daily_insights = [
        {"title": "AI Hiring Surge", "desc": "Top tech companies increased AI hiring by 40% this quarter. Python and TensorFlow skills most sought after.", "trend": "up"},
        {"title": "Cloud Demand Peak", "desc": "AWS and Azure certifications see 35% more job postings. Multi-cloud expertise highly valued.", "trend": "up"},
        {"title": "Cybersecurity Alert", "desc": "Security professionals in high demand with 500K+ unfilled positions in India alone.", "trend": "up"},
        {"title": "Data Science Boom", "desc": "Companies investing heavily in data analytics. SQL and Python remain most requested skills.", "trend": "up"},
        {"title": "DevOps Evolution", "desc": "GitOps and Platform Engineering emerging as hot specializations in DevOps field.", "trend": "up"},
        {"title": "Startup Funding Up", "desc": "Indian startups raised $2B+ this month, creating 50K+ new tech positions.", "trend": "up"},
        {"title": "Remote Jobs Growing", "desc": "67% of tech companies now offer remote or hybrid options. Location no longer a barrier.", "trend": "up"},
    ]
    
    # Select today's content based on day of year
    tip_index = day_of_year % len(daily_tips)
    insight_index = day_of_year % len(daily_insights)
    
    # Get 3 tips starting from today's index
    today_tips = [daily_tips[(tip_index + i) % len(daily_tips)] for i in range(3)]
    today_insight = daily_insights[insight_index]
    
    # Dynamic stats that change slightly each day
    base_ai_jobs = 1200000
    base_cyber_jobs = 500000
    base_data_jobs = 800000
    
    # Small daily variations (±5%)
    variation = (day_of_year % 10) / 100
    ai_jobs = int(base_ai_jobs * (1 + variation))
    cyber_jobs = int(base_cyber_jobs * (1 + variation))
    data_jobs = int(base_data_jobs * (1 + variation))
    
    market_data = {
        'update_date': datetime.now().strftime('%d %b %Y'),
        'daily_insight': today_insight,
        'daily_tips': today_tips,
        'ai_jobs': f"{ai_jobs/1000000:.1f}M+" if ai_jobs >= 1000000 else f"{ai_jobs/1000}K+",
        'cyber_jobs': f"{cyber_jobs/1000}K+",
        'data_jobs': f"{data_jobs/1000}K+",
    }
    
    return render_template('job_market.html', user=user, market_data=market_data)


@app.route('/chat')
def chat_page():
    """Chat with AI mentor page."""
    return render_template('chat.html')


@app.route('/scam-detector')
def scam_detector_page():
    """Scam detector page."""
    return render_template('scam_detector.html')


@app.route('/behaviour-analysis')
def behaviour_analysis_page():
    """Interview behaviour analysis page for mock interview practice."""
    user = get_current_user()
    return render_template('behaviour_analysis.html', user=user)
    return render_template('scam_detector.html')


@app.route('/personality')
def personality_page():
    """Personality profiler page."""
    return redirect(url_for('onboarding'))


@app.route('/salary-predictor')
def salary_predictor_page():
    """Salary predictor page."""
    return redirect(url_for('results_page'))


# ============== Authentication Routes ==============

@app.route('/login', methods=['GET'])
def login_page():
    """Login page with modern app design."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = request.args.get('error')
    success = request.args.get('success')
    return render_template('auth_login.html', error=error, success=success)


@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission."""
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    remember = request.form.get('remember') == 'on'
    
    if not email or not password:
        return render_template('auth_login.html', error='Please enter both email and password.')
    
    user = User.authenticate(email, password)
    print(f"Login attempt for {email}: {'Success' if user else 'Failed'}")
    
    if user:
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        session['education_level'] = user.education_level or ''
        
        # Create session token for API access
        token = UserSession.create(user.id)
        session['api_token'] = token
        
        if remember:
            session.permanent = True
        
        # Redirect to a login success page that stores token in localStorage
        return redirect(url_for('login_success', token=token, user_id=user.id, name=user.name, email=user.email))
    else:
        return render_template('auth_login.html', error='Invalid email or password.')


@app.route('/login-success')
def login_success():
    """Intermediate page to store login token in localStorage for Simple Browser compatibility."""
    token = request.args.get('token', '')
    user_id = request.args.get('user_id', '')
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    return render_template('login_success.html', token=token, user_id=user_id, name=name, email=email)


@app.route('/signup', methods=['GET'])
def signup_page():
    """Sign up page with modern design."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    error = request.args.get('error')
    return render_template('auth_signup.html', error=error)


@app.route('/signup', methods=['POST'])
def signup():
    """Handle signup form submission."""
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    education_level = request.form.get('education_level', '')
    stream = request.form.get('stream', '')
    field = request.form.get('field', '')
    
    # Validation
    if not all([first_name, email, password, education_level]):
        return render_template('auth_signup.html', error='Please fill in all required fields.')
    
    if len(password) < 8:
        return render_template('auth_signup.html', error='Password must be at least 8 characters.')
    
    # Check if email exists
    existing_user = User.get_by_email(email)
    if existing_user:
        return render_template('auth_signup.html', error='An account with this email already exists.')
    
    # Create user
    name = f"{first_name} {last_name}"
    
    user = User.create(email, password, name, education_level=education_level)
    if user:
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login_page', success='Account created! Please login.'))
    else:
        return render_template('auth_signup.html', error='Failed to create account. Please try again.')


@app.route('/logout')
def logout():
    """Log out the current user."""
    if 'api_token' in session:
        UserSession.delete(session['api_token'])
    session.clear()
    # Redirect to logout page that clears localStorage
    return redirect(url_for('logout_page'))


@app.route('/logout-complete')
def logout_page():
    """Page that clears localStorage and redirects to login."""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logging out...</title>
        <script>
            localStorage.removeItem('cariax_token');
            localStorage.removeItem('cariax_user_id');
            localStorage.removeItem('cariax_user_name');
            localStorage.removeItem('cariax_user_email');
            localStorage.removeItem('cariax_logged_in');
            window.location.href = '/login';
        </script>
    </head>
    <body>Logging out...</body>
    </html>
    '''


@app.route('/profile')
def profile_page():
    """User profile page."""
    user = get_current_user()
    
    # If no session, allow page to load and use localStorage data
    if not user:
        # Render profile with empty user - JavaScript will populate from localStorage
        return render_template('profile.html', user=None, results=[])
    
    # Get user's assessment history
    results = AssessmentResult.get_user_results(user.id)
    return render_template('profile.html', user=user, results=results)


@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    user_id = session.get('user_id')
    
    updates = {
        'name': request.form.get('name', '').strip(),
        'profile_data': json.dumps({
            'education_level': request.form.get('education_level', ''),
            'stream': request.form.get('stream', ''),
            'field': request.form.get('field', ''),
            'phone': request.form.get('phone', ''),
            'city': request.form.get('city', '')
        })
    }
    
    if User.update_profile(user_id, updates):
        flash('Profile updated successfully!', 'success')
    else:
        flash('Failed to update profile.', 'error')
    
    return redirect(url_for('profile_page'))


# ============== OAuth Routes ==============

@app.route('/auth/google')
def auth_google():
    """Initiate Google OAuth flow."""
    config = OAUTH_CONFIG['google']
    if not config['client_id']:
        flash('Google OAuth is not configured.', 'error')
        return redirect(url_for('login_page'))
    
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    auth_url = (
        f"{config['auth_url']}?"
        f"client_id={config['client_id']}&"
        f"redirect_uri={config['redirect_uri']}&"
        f"response_type=code&"
        f"scope={config['scope']}&"
        f"state={state}"
    )
    return redirect(auth_url)


@app.route('/auth/google/callback')
def auth_google_callback():
    """Handle Google OAuth callback."""
    import requests
    
    # Check for OAuth errors
    error = request.args.get('error')
    if error:
        print(f"Google OAuth error: {error}")
        return redirect(url_for('login_page', error=f'Google login failed: {error}'))
    
    config = OAUTH_CONFIG['google']
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return redirect(url_for('login_page', error='No authorization code received from Google'))
    
    if state != session.get('oauth_state'):
        return redirect(url_for('login_page', error='Invalid OAuth state. Please try again.'))
    
    try:
        # Exchange code for token
        token_response = requests.post(config['token_url'], data={
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': config['redirect_uri']
        }, timeout=10)
        token_data = token_response.json()
        
        if 'access_token' not in token_data:
            print(f"Google token error: {token_data}")
            return redirect(url_for('login_page', error='Failed to get access token from Google'))
        
        # Get user info
        userinfo_response = requests.get(
            config['userinfo_url'],
            headers={'Authorization': f"Bearer {token_data['access_token']}"},
            timeout=10
        )
        userinfo = userinfo_response.json()
        
        if not userinfo.get('email'):
            return redirect(url_for('login_page', error='Could not get email from Google'))
        
        # Create or get user
        user = User.create_oauth(
            email=userinfo.get('email'),
            name=userinfo.get('name') or userinfo.get('email').split('@')[0],
            provider='google',
            oauth_id=str(userinfo.get('id')),
            profile_picture=userinfo.get('picture')
        )
        
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            token = UserSession.create(user.id)
            session['api_token'] = token
            # Redirect through login_success to set localStorage
            return redirect(url_for('login_success', token=token, user_id=user.id, name=user.name, email=user.email))
        
        return redirect(url_for('login_page', error='Failed to create user account'))
        
    except requests.exceptions.Timeout:
        return redirect(url_for('login_page', error='Google authentication timed out. Please try again.'))
    except Exception as e:
        print(f"Google OAuth exception: {str(e)}")
        return redirect(url_for('login_page', error='An error occurred during Google login'))


@app.route('/auth/github')
def auth_github():
    """Initiate GitHub OAuth flow."""
    config = OAUTH_CONFIG['github']
    if not config['client_id']:
        flash('GitHub OAuth is not configured.', 'error')
        return redirect(url_for('login_page'))
    
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    auth_url = (
        f"{config['auth_url']}?"
        f"client_id={config['client_id']}&"
        f"redirect_uri={config['redirect_uri']}&"
        f"scope={config['scope']}&"
        f"state={state}"
    )
    return redirect(auth_url)


@app.route('/auth/github/callback')
def auth_github_callback():
    """Handle GitHub OAuth callback."""
    import requests
    
    # Check for OAuth errors
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', error)
        print(f"GitHub OAuth error: {error_description}")
        return redirect(url_for('login_page', error=f'GitHub login failed: {error_description}'))
    
    config = OAUTH_CONFIG['github']
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return redirect(url_for('login_page', error='No authorization code received from GitHub'))
    
    if state != session.get('oauth_state'):
        return redirect(url_for('login_page', error='Invalid OAuth state. Please try again.'))
    
    try:
        # Exchange code for token
        token_response = requests.post(
            config['token_url'],
            data={
                'client_id': config['client_id'],
                'client_secret': config['client_secret'],
                'code': code
            },
            headers={'Accept': 'application/json'},
            timeout=10
        )
        token_data = token_response.json()
        
        if 'access_token' not in token_data:
            print(f"GitHub token error: {token_data}")
            return redirect(url_for('login_page', error='Failed to get access token from GitHub'))
        
        # Get user info
        userinfo = requests.get(
            config['userinfo_url'],
            headers={'Authorization': f"token {token_data['access_token']}"},
            timeout=10
        ).json()
        
        # Get user email (might be private)
        emails_response = requests.get(
            'https://api.github.com/user/emails',
            headers={'Authorization': f"token {token_data['access_token']}"},
            timeout=10
        )
        emails = emails_response.json() if emails_response.status_code == 200 else []
        
        email = userinfo.get('email')
        if not email and isinstance(emails, list) and emails:
            primary_emails = [e for e in emails if e.get('primary')]
            if primary_emails:
                email = primary_emails[0].get('email')
            elif emails:
                email = emails[0].get('email')
        
        if not email:
            return redirect(url_for('login_page', error='Could not get email from GitHub. Please make sure your email is public or try another login method.'))
        
        # Create or get user
        user = User.create_oauth(
            email=email,
            name=userinfo.get('name') or userinfo.get('login'),
            provider='github',
            oauth_id=str(userinfo.get('id')),
            profile_picture=userinfo.get('avatar_url')
        )
        
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_email'] = user.email
            token = UserSession.create(user.id)
            session['api_token'] = token
            # Redirect through login_success to set localStorage
            return redirect(url_for('login_success', token=token, user_id=user.id, name=user.name, email=user.email))
        
        return redirect(url_for('login_page', error='Failed to create user account'))
        
    except requests.exceptions.Timeout:
        return redirect(url_for('login_page', error='GitHub authentication timed out. Please try again.'))
    except Exception as e:
        print(f"GitHub OAuth exception: {str(e)}")
        return redirect(url_for('login_page', error='An error occurred during GitHub login'))


# ============== Assessment Questions API ==============

# Career recommendations by specialization
CAREER_BY_SPECIALIZATION = {
    # Computer Science & Engineering
    'cse': [
        {'name': 'Software Engineer', 'salary': {'entry': 800000, 'mid': 1800000, 'senior': 4000000}, 'description': 'Design, develop, and maintain software applications and systems.', 'skills': ['Python', 'Java', 'System Design', 'Problem Solving']},
        {'name': 'Full Stack Developer', 'salary': {'entry': 700000, 'mid': 1500000, 'senior': 3500000}, 'description': 'Build complete web applications handling both frontend and backend development.', 'skills': ['React', 'Node.js', 'MongoDB', 'AWS']},
        {'name': 'DevOps Engineer', 'salary': {'entry': 900000, 'mid': 2000000, 'senior': 4500000}, 'description': 'Streamline software development and IT operations through automation and CI/CD.', 'skills': ['Docker', 'Kubernetes', 'Jenkins', 'Linux']},
        {'name': 'Cloud Solutions Architect', 'salary': {'entry': 1200000, 'mid': 2500000, 'senior': 5000000}, 'description': 'Design and implement cloud infrastructure and solutions for enterprises.', 'skills': ['AWS', 'Azure', 'GCP', 'Terraform']},
        {'name': 'Cybersecurity Analyst', 'salary': {'entry': 800000, 'mid': 1700000, 'senior': 3500000}, 'description': 'Protect organizations from cyber threats and security breaches.', 'skills': ['Network Security', 'Ethical Hacking', 'SIEM', 'Incident Response']}
    ],
    # AI & Machine Learning
    'ai_ml': [
        {'name': 'Machine Learning Engineer', 'salary': {'entry': 1200000, 'mid': 2500000, 'senior': 5000000}, 'description': 'Build and deploy machine learning models for real-world applications.', 'skills': ['TensorFlow', 'PyTorch', 'Python', 'Deep Learning']},
        {'name': 'Data Scientist', 'salary': {'entry': 1000000, 'mid': 2200000, 'senior': 4500000}, 'description': 'Extract insights from complex data using statistical and ML techniques.', 'skills': ['Python', 'R', 'Statistics', 'Machine Learning']},
        {'name': 'AI Research Scientist', 'salary': {'entry': 1500000, 'mid': 3000000, 'senior': 6000000}, 'description': 'Conduct cutting-edge research to advance AI capabilities.', 'skills': ['Deep Learning', 'NLP', 'Computer Vision', 'Research']},
        {'name': 'NLP Engineer', 'salary': {'entry': 1100000, 'mid': 2300000, 'senior': 4800000}, 'description': 'Develop natural language processing systems for text and speech.', 'skills': ['NLP', 'Transformers', 'BERT/GPT', 'Python']},
        {'name': 'Computer Vision Engineer', 'salary': {'entry': 1100000, 'mid': 2400000, 'senior': 5000000}, 'description': 'Build systems that can interpret and analyze visual information.', 'skills': ['OpenCV', 'CNN', 'Image Processing', 'PyTorch']}
    ],
    # Biomedical Engineering
    'biomedical': [
        {'name': 'Biomedical Engineer', 'salary': {'entry': 600000, 'mid': 1400000, 'senior': 3000000}, 'description': 'Design medical devices and equipment to improve healthcare.', 'skills': ['Medical Devices', 'CAD', 'Biomaterials', 'Regulatory']},
        {'name': 'Clinical Engineer', 'salary': {'entry': 550000, 'mid': 1200000, 'senior': 2500000}, 'description': 'Manage and maintain medical equipment in healthcare facilities.', 'skills': ['Equipment Maintenance', 'Hospital Systems', 'Quality Control', 'Training']},
        {'name': 'Medical Device Designer', 'salary': {'entry': 700000, 'mid': 1500000, 'senior': 3200000}, 'description': 'Design innovative medical devices from concept to production.', 'skills': ['3D Modeling', 'Prototyping', 'FDA Regulations', 'Materials Science']},
        {'name': 'Tissue Engineer', 'salary': {'entry': 650000, 'mid': 1400000, 'senior': 2800000}, 'description': 'Develop biological tissues and organs for transplantation and research.', 'skills': ['Cell Culture', 'Biomaterials', 'Regenerative Medicine', 'Research']},
        {'name': 'Rehabilitation Engineer', 'salary': {'entry': 550000, 'mid': 1200000, 'senior': 2400000}, 'description': 'Create assistive technologies for people with disabilities.', 'skills': ['Prosthetics', 'Orthotics', 'Assistive Tech', 'Patient Care']}
    ],
    # Mechanical Engineering
    'mechanical': [
        {'name': 'Mechanical Design Engineer', 'salary': {'entry': 500000, 'mid': 1200000, 'senior': 2800000}, 'description': 'Design mechanical systems and components using CAD software.', 'skills': ['CAD', 'SolidWorks', 'CATIA', 'Product Design']},
        {'name': 'Automotive Engineer', 'salary': {'entry': 600000, 'mid': 1400000, 'senior': 3200000}, 'description': 'Design and develop vehicles and automotive systems.', 'skills': ['Vehicle Dynamics', 'Powertrain', 'MATLAB', 'Testing']},
        {'name': 'Manufacturing Engineer', 'salary': {'entry': 550000, 'mid': 1300000, 'senior': 2800000}, 'description': 'Optimize manufacturing processes for efficiency and quality.', 'skills': ['Lean Manufacturing', 'Six Sigma', 'Process Optimization', 'Quality Control']},
        {'name': 'HVAC Engineer', 'salary': {'entry': 500000, 'mid': 1100000, 'senior': 2400000}, 'description': 'Design heating, ventilation, and air conditioning systems.', 'skills': ['HVAC Design', 'Energy Efficiency', 'Building Codes', 'AutoCAD']},
        {'name': 'Robotics Engineer', 'salary': {'entry': 700000, 'mid': 1600000, 'senior': 3500000}, 'description': 'Design, build, and program robotic systems for various applications.', 'skills': ['Robotics', 'PLC Programming', 'Automation', 'Control Systems']}
    ],
    # Electronics & Communication
    'electronics': [
        {'name': 'Electronics Engineer', 'salary': {'entry': 500000, 'mid': 1200000, 'senior': 2800000}, 'description': 'Design and develop electronic circuits and systems.', 'skills': ['Circuit Design', 'PCB Layout', 'Embedded Systems', 'Testing']},
        {'name': 'Embedded Systems Engineer', 'salary': {'entry': 600000, 'mid': 1400000, 'senior': 3200000}, 'description': 'Develop software and hardware for embedded devices.', 'skills': ['C/C++', 'Microcontrollers', 'RTOS', 'Debugging']},
        {'name': 'VLSI Design Engineer', 'salary': {'entry': 700000, 'mid': 1600000, 'senior': 3800000}, 'description': 'Design integrated circuits and semiconductor devices.', 'skills': ['Verilog', 'VHDL', 'ASIC Design', 'Cadence Tools']},
        {'name': 'RF Engineer', 'salary': {'entry': 600000, 'mid': 1400000, 'senior': 3200000}, 'description': 'Design and optimize radio frequency systems for wireless communication.', 'skills': ['RF Design', 'Antenna Design', 'Signal Processing', 'Testing']},
        {'name': 'IoT Solutions Architect', 'salary': {'entry': 800000, 'mid': 1800000, 'senior': 4000000}, 'description': 'Design and implement Internet of Things solutions for various industries.', 'skills': ['IoT Platforms', 'Sensors', 'Cloud', 'Security']}
    ],
    # BDS - Dental Surgery
    'bds': [
        {'name': 'Dental Surgeon', 'salary': {'entry': 600000, 'mid': 1500000, 'senior': 4000000}, 'description': 'Perform dental surgeries and provide comprehensive oral healthcare.', 'skills': ['Oral Surgery', 'Diagnosis', 'Patient Care', 'Clinical Skills']},
        {'name': 'Orthodontist', 'salary': {'entry': 800000, 'mid': 2000000, 'senior': 5000000}, 'description': 'Specialize in teeth alignment and corrective procedures.', 'skills': ['Braces', 'Invisalign', 'Jaw Alignment', 'Treatment Planning']},
        {'name': 'Endodontist', 'salary': {'entry': 700000, 'mid': 1800000, 'senior': 4500000}, 'description': 'Specialize in root canal treatments and dental pulp procedures.', 'skills': ['Root Canal', 'Microsurgery', 'Pain Management', 'Diagnosis']},
        {'name': 'Prosthodontist', 'salary': {'entry': 750000, 'mid': 1900000, 'senior': 4800000}, 'description': 'Replace missing teeth with crowns, bridges, and implants.', 'skills': ['Implants', 'Crowns', 'Dentures', 'Cosmetic Dentistry']},
        {'name': 'Pediatric Dentist', 'salary': {'entry': 650000, 'mid': 1600000, 'senior': 4000000}, 'description': 'Provide dental care specifically for children and adolescents.', 'skills': ['Child Care', 'Preventive Dentistry', 'Behavior Management', 'Communication']}
    ],
    # Nursing Sciences
    'nursing': [
        {'name': 'Registered Nurse', 'salary': {'entry': 350000, 'mid': 600000, 'senior': 1200000}, 'description': 'Provide direct patient care and coordinate with healthcare teams.', 'skills': ['Patient Care', 'Clinical Skills', 'Communication', 'Critical Thinking']},
        {'name': 'ICU Nurse', 'salary': {'entry': 450000, 'mid': 800000, 'senior': 1500000}, 'description': 'Specialize in critical care for seriously ill patients in intensive care units.', 'skills': ['Critical Care', 'Ventilator Care', 'Emergency Response', 'Monitoring']},
        {'name': 'Nurse Practitioner', 'salary': {'entry': 600000, 'mid': 1200000, 'senior': 2500000}, 'description': 'Provide advanced nursing care and can prescribe medications.', 'skills': ['Diagnosis', 'Treatment Planning', 'Prescribing', 'Patient Education']},
        {'name': 'Nurse Educator', 'salary': {'entry': 500000, 'mid': 1000000, 'senior': 2000000}, 'description': 'Train and educate nursing students and healthcare staff.', 'skills': ['Teaching', 'Curriculum Development', 'Clinical Expertise', 'Mentoring']},
        {'name': 'Nurse Manager', 'salary': {'entry': 550000, 'mid': 1100000, 'senior': 2200000}, 'description': 'Lead nursing teams and manage healthcare operations.', 'skills': ['Leadership', 'Management', 'Staffing', 'Quality Improvement']}
    ],
    # MBBS - General Medicine
    'mbbs': [
        {'name': 'General Physician', 'salary': {'entry': 800000, 'mid': 1800000, 'senior': 4000000}, 'description': 'Diagnose and treat patients with various medical conditions.', 'skills': ['Diagnosis', 'Patient Care', 'Clinical Skills', 'Communication']},
        {'name': 'Cardiologist', 'salary': {'entry': 1200000, 'mid': 3000000, 'senior': 8000000}, 'description': 'Specialize in diagnosing and treating heart diseases.', 'skills': ['Cardiology', 'ECG', 'Interventional Procedures', 'Patient Care']},
        {'name': 'Neurologist', 'salary': {'entry': 1100000, 'mid': 2800000, 'senior': 7000000}, 'description': 'Treat disorders of the nervous system including brain and spinal cord.', 'skills': ['Neurology', 'EEG', 'Clinical Examination', 'Research']},
        {'name': 'Pediatrician', 'salary': {'entry': 900000, 'mid': 2200000, 'senior': 5000000}, 'description': 'Provide healthcare for infants, children, and adolescents.', 'skills': ['Child Care', 'Immunization', 'Growth Assessment', 'Communication']},
        {'name': 'Emergency Medicine Specialist', 'salary': {'entry': 1000000, 'mid': 2500000, 'senior': 5500000}, 'description': 'Handle critical and emergency medical situations.', 'skills': ['Trauma Care', 'Quick Decision Making', 'Critical Care', 'Emergency Procedures']}
    ],
    # Pharm.D - Clinical Pharmacy
    'pharm_d': [
        {'name': 'Clinical Pharmacist', 'salary': {'entry': 600000, 'mid': 1200000, 'senior': 2500000}, 'description': 'Provide patient-centered medication therapy management.', 'skills': ['Drug Therapy', 'Patient Counseling', 'Clinical Assessment', 'Drug Interactions']},
        {'name': 'Hospital Pharmacist', 'salary': {'entry': 550000, 'mid': 1100000, 'senior': 2200000}, 'description': 'Manage medication distribution and safety in hospital settings.', 'skills': ['Dispensing', 'Inventory Management', 'Drug Safety', 'Teamwork']},
        {'name': 'Pharmaceutical Scientist', 'salary': {'entry': 700000, 'mid': 1500000, 'senior': 3000000}, 'description': 'Research and develop new pharmaceutical drugs and treatments.', 'skills': ['Drug Development', 'Clinical Trials', 'Research', 'Regulatory Affairs']},
        {'name': 'Pharmacovigilance Specialist', 'salary': {'entry': 650000, 'mid': 1400000, 'senior': 2800000}, 'description': 'Monitor drug safety and adverse effects after market release.', 'skills': ['Safety Monitoring', 'Data Analysis', 'Regulatory Reporting', 'Risk Assessment']},
        {'name': 'Drug Regulatory Affairs Manager', 'salary': {'entry': 800000, 'mid': 1800000, 'senior': 3500000}, 'description': 'Ensure pharmaceutical products meet regulatory requirements.', 'skills': ['FDA/CDSCO', 'Documentation', 'Compliance', 'Submissions']}
    ],
    # Data Science
    'data_science': [
        {'name': 'Data Scientist', 'salary': {'entry': 900000, 'mid': 2000000, 'senior': 4200000}, 'description': 'Analyze complex data to derive actionable business insights.', 'skills': ['Python', 'Statistics', 'Machine Learning', 'SQL']},
        {'name': 'Data Analyst', 'salary': {'entry': 600000, 'mid': 1300000, 'senior': 2800000}, 'description': 'Collect, process, and analyze data to support decision-making.', 'skills': ['SQL', 'Excel', 'Tableau', 'Statistics']},
        {'name': 'Business Intelligence Analyst', 'salary': {'entry': 700000, 'mid': 1500000, 'senior': 3200000}, 'description': 'Create dashboards and reports for data-driven business decisions.', 'skills': ['Power BI', 'Tableau', 'SQL', 'Data Visualization']},
        {'name': 'Data Engineer', 'salary': {'entry': 800000, 'mid': 1800000, 'senior': 4000000}, 'description': 'Build and maintain data pipelines and infrastructure.', 'skills': ['Python', 'Spark', 'ETL', 'Cloud Platforms']},
        {'name': 'Analytics Manager', 'salary': {'entry': 1000000, 'mid': 2200000, 'senior': 4500000}, 'description': 'Lead analytics teams and drive data strategy for organizations.', 'skills': ['Leadership', 'Analytics', 'Strategy', 'Communication']}
    ],
    # Marketing Management
    'marketing': [
        {'name': 'Digital Marketing Manager', 'salary': {'entry': 600000, 'mid': 1400000, 'senior': 3000000}, 'description': 'Lead digital marketing campaigns across multiple channels.', 'skills': ['SEO', 'SEM', 'Social Media', 'Analytics']},
        {'name': 'Brand Manager', 'salary': {'entry': 700000, 'mid': 1600000, 'senior': 3500000}, 'description': 'Develop and maintain brand identity and positioning.', 'skills': ['Brand Strategy', 'Market Research', 'Communication', 'Creative Thinking']},
        {'name': 'Content Marketing Specialist', 'salary': {'entry': 500000, 'mid': 1100000, 'senior': 2400000}, 'description': 'Create and manage content strategies to engage audiences.', 'skills': ['Content Creation', 'SEO', 'Social Media', 'Analytics']},
        {'name': 'Product Marketing Manager', 'salary': {'entry': 800000, 'mid': 1800000, 'senior': 4000000}, 'description': 'Position products in the market and drive go-to-market strategies.', 'skills': ['Product Positioning', 'Market Analysis', 'GTM Strategy', 'Communication']},
        {'name': 'Growth Marketing Manager', 'salary': {'entry': 750000, 'mid': 1700000, 'senior': 3800000}, 'description': 'Drive customer acquisition and retention through data-driven marketing.', 'skills': ['Growth Hacking', 'A/B Testing', 'Analytics', 'Automation']}
    ],
    # Psychology
    'psychology': [
        {'name': 'Clinical Psychologist', 'salary': {'entry': 500000, 'mid': 1100000, 'senior': 2500000}, 'description': 'Diagnose and treat mental health disorders through therapy.', 'skills': ['Psychotherapy', 'Assessment', 'Counseling', 'Research']},
        {'name': 'Organizational Psychologist', 'salary': {'entry': 600000, 'mid': 1400000, 'senior': 3000000}, 'description': 'Improve workplace productivity and employee well-being.', 'skills': ['I-O Psychology', 'Assessment', 'Training', 'Consulting']},
        {'name': 'Counseling Psychologist', 'salary': {'entry': 450000, 'mid': 1000000, 'senior': 2200000}, 'description': 'Help individuals cope with personal and emotional challenges.', 'skills': ['Counseling', 'Empathy', 'Active Listening', 'Crisis Intervention']},
        {'name': 'Child Psychologist', 'salary': {'entry': 480000, 'mid': 1050000, 'senior': 2300000}, 'description': 'Specialize in mental health assessment and treatment for children.', 'skills': ['Child Development', 'Play Therapy', 'Family Counseling', 'Assessment']},
        {'name': 'Neuropsychologist', 'salary': {'entry': 700000, 'mid': 1500000, 'senior': 3200000}, 'description': 'Study the relationship between brain function and behavior.', 'skills': ['Neuropsychological Testing', 'Research', 'Rehabilitation', 'Assessment']}
    ],
    # Default careers
    'default': [
        {'name': 'Business Analyst', 'salary': {'entry': 600000, 'mid': 1300000, 'senior': 2800000}, 'description': 'Analyze business processes and recommend improvements.', 'skills': ['Analysis', 'Communication', 'Problem Solving', 'Documentation']},
        {'name': 'Project Manager', 'salary': {'entry': 700000, 'mid': 1500000, 'senior': 3200000}, 'description': 'Lead projects from initiation to successful completion.', 'skills': ['Leadership', 'Planning', 'Communication', 'Risk Management']},
        {'name': 'Management Consultant', 'salary': {'entry': 900000, 'mid': 2000000, 'senior': 4500000}, 'description': 'Advise organizations on strategy and operational improvements.', 'skills': ['Strategy', 'Analysis', 'Presentation', 'Problem Solving']},
        {'name': 'Human Resources Manager', 'salary': {'entry': 600000, 'mid': 1300000, 'senior': 2800000}, 'description': 'Manage employee relations and organizational development.', 'skills': ['HR Policies', 'Recruitment', 'Employee Relations', 'Compliance']},
        {'name': 'Operations Manager', 'salary': {'entry': 650000, 'mid': 1400000, 'senior': 3000000}, 'description': 'Oversee daily operations and optimize business processes.', 'skills': ['Operations', 'Leadership', 'Process Improvement', 'Budgeting']}
    ]
}

def get_careers_for_specialization(specialization, stream, domain_answers, personality_data, skills_data, academics_data):
    """
    Get career recommendations based on specialization and comprehensive assessment.
    
    Scoring is based on:
    - Domain quiz performance (40%)
    - Personality traits match (25%)
    - Skills self-rating (20%)
    - Academic performance (15%)
    """
    # Get base careers for specialization
    careers = CAREER_BY_SPECIALIZATION.get(specialization, 
              CAREER_BY_SPECIALIZATION.get(stream, 
              CAREER_BY_SPECIALIZATION['default']))
    
    # ============ 1. DOMAIN QUIZ SCORE (40% weight) ============
    # First option is always correct in our quiz design
    correct_answers = 0
    total_questions = len(domain_answers) if domain_answers else 25
    
    # Correct answers mapping (first option is correct for each question)
    correct_answer_map = {
        # CSE
        'cse1': 'O(log n)', 'cse2': 'Stack', 'cse3': 'Structured Query Language',
        'cse4': 'Compilation', 'cse5': 'Track code changes', 'cse6': 'Merge Sort',
        'cse7': 'Web service architecture', 'cse8': 'Hyper Text Markup Language',
        'cse9': 'MongoDB', 'cse10': 'Function calling itself',
        # AI/ML
        'ai1': 'Learning with labeled data', 'ai2': 'Human brain', 'ai3': 'Model too specific to training data',
        'ai4': 'TensorFlow', 'ai5': 'Natural Language Processing',
        # Mechanical
        'mech1': 'Study of heat and energy', 'mech2': 'Computer-aided design',
        'mech3': 'Force per unit area', 'mech4': 'Deformation due to stress',
        # Electronics
        'elec1': 'Material with controllable conductivity', 'elec2': 'Electronic switch/amplifier',
        'elec3': 'Binary signal processing', 'elec4': 'Small computer on chip',
        # Biomedical
        'bio1': 'Engineering for healthcare', 'bio2': 'Magnetic Resonance Imaging',
        'bio3': 'Artificial body parts', 'bio4': 'Study of body mechanics',
        # MBBS
        'mbbs1': 'Study of body structure', 'mbbs2': 'Study of body functions',
        'mbbs3': 'Study of diseases', 'mbbs4': 'Study of drugs',
        # Pharm D
        'phar1': 'Drug movement in body', 'phar2': 'Effect of multiple drugs together',
        'phar3': 'Measuring drug levels in blood', 'phar4': 'Patient-focused pharmacy',
        # BDS
        'bds1': 'Study of mouth structure', 'bds2': 'Tooth decay',
        'bds3': 'Gum disease treatment', 'bds4': 'Teeth alignment treatment',
        # Nursing
        'nur1': 'Attending to patient needs', 'nur2': 'Checking temperature, pulse, BP',
        'nur3': 'Covering and treating wounds', 'nur4': 'Giving medicines to patients',
        # Psychology
        'psy1': 'Study of mental processes', 'psy2': 'Study of observable behavior',
        # Marketing
        'mkt1': 'Dividing market into groups', 'mkt2': 'How brand is perceived',
        # Data Science
        'ds1': 'Graphical data representation', 'ds2': 'Data analysis & modeling',
    }
    
    for q_id, answer in domain_answers.items():
        # Check if the answer is the first option (correct answer)
        if q_id in correct_answer_map:
            if answer == correct_answer_map[q_id]:
                correct_answers += 1
        else:
            # For questions not in map, assume first option pattern
            correct_answers += 0.5  # Give partial credit
    
    quiz_score = (correct_answers / max(total_questions, 1)) * 100
    print(f"   Quiz Score: {correct_answers}/{total_questions} = {quiz_score:.1f}%")
    
    # ============ 2. PERSONALITY SCORE (25% weight) ============
    # Analyze personality traits for career matching
    personality_traits = {
        'leadership': 0,
        'analytical': 0,
        'creative': 0,
        'teamwork': 0,
        'independent': 0
    }
    
    if personality_data:
        for q_id, answer in personality_data.items():
            if 'Lead' in str(answer) or 'decisive' in str(answer).lower():
                personality_traits['leadership'] += 1
            if 'Logical' in str(answer) or 'analytical' in str(answer).lower() or 'thorough' in str(answer).lower():
                personality_traits['analytical'] += 1
            if 'Creative' in str(answer) or 'intuition' in str(answer).lower():
                personality_traits['creative'] += 1
            if 'team' in str(answer).lower() or 'collaborative' in str(answer).lower():
                personality_traits['teamwork'] += 1
            if 'Independent' in str(answer) or 'alone' in str(answer).lower():
                personality_traits['independent'] += 1
    
    print(f"   Personality traits: {personality_traits}")
    
    # ============ 3. SKILLS SCORE (20% weight) ============
    avg_skill_rating = 2.5  # Default mid-range
    if skills_data:
        total_skills = 0
        skill_count = 0
        for skill, rating in skills_data.items():
            if isinstance(rating, (int, float)):
                total_skills += rating
                skill_count += 1
        if skill_count > 0:
            avg_skill_rating = total_skills / skill_count
    
    skills_score = (avg_skill_rating / 4) * 100  # Assuming 1-4 scale
    print(f"   Skills Score: {avg_skill_rating}/4 = {skills_score:.1f}%")
    
    # ============ 4. ACADEMICS SCORE (15% weight) ============
    avg_marks = 70  # Default
    if academics_data:
        total_marks = 0
        subject_count = 0
        for subject in academics_data:
            if isinstance(subject, dict) and 'marks' in subject:
                total_marks += int(subject['marks'])
                subject_count += 1
        if subject_count > 0:
            avg_marks = total_marks / subject_count
    
    academics_score = avg_marks
    print(f"   Academics Score: {academics_score:.1f}%")
    
    # ============ CALCULATE WEIGHTED FINAL SCORES ============
    result = []
    
    # Career-specific trait requirements
    career_traits = {
        'Software Engineer': {'analytical': 2, 'independent': 1},
        'Full Stack Developer': {'analytical': 1, 'creative': 1, 'teamwork': 1},
        'DevOps Engineer': {'analytical': 2, 'teamwork': 1},
        'Machine Learning Engineer': {'analytical': 2, 'creative': 1},
        'Data Scientist': {'analytical': 2, 'creative': 1},
        'Mechanical Design Engineer': {'analytical': 1, 'creative': 2},
        'Automotive Engineer': {'analytical': 1, 'teamwork': 1, 'creative': 1},
        'General Physician': {'analytical': 1, 'teamwork': 2, 'leadership': 1},
        'Cardiologist': {'analytical': 2, 'leadership': 1},
        'Clinical Pharmacist': {'analytical': 2, 'teamwork': 1},
        'Dental Surgeon': {'analytical': 1, 'independent': 1, 'creative': 1},
        'Registered Nurse': {'teamwork': 2, 'leadership': 1},
        'ICU Nurse': {'analytical': 1, 'teamwork': 2},
        'Digital Marketing Manager': {'creative': 2, 'leadership': 1},
        'Clinical Psychologist': {'analytical': 1, 'teamwork': 1, 'creative': 1},
        'Electronics Engineer': {'analytical': 2, 'creative': 1},
        'Biomedical Engineer': {'analytical': 1, 'creative': 1, 'teamwork': 1},
    }
    
    for idx, career in enumerate(careers):
        career_name = career['name']
        
        # Base weighted score
        base_score = (
            quiz_score * 0.40 +
            skills_score * 0.20 +
            academics_score * 0.15
        )
        
        # Personality matching (25%)
        personality_match = 50  # Default match
        required_traits = career_traits.get(career_name, {})
        if required_traits:
            trait_match = 0
            trait_total = 0
            for trait, weight in required_traits.items():
                trait_match += personality_traits.get(trait, 0) * weight
                trait_total += weight
            if trait_total > 0:
                personality_match = min(100, (trait_match / trait_total) * 50 + 50)
        
        base_score += personality_match * 0.25
        
        # Add variation based on career position (top careers slightly higher)
        position_bonus = max(0, (5 - idx) * 2)
        
        # Add randomness based on quiz performance
        quiz_bonus = (correct_answers % 5) * 1.5
        
        final_score = min(98, max(55, base_score + position_bonus + quiz_bonus))
        
        # Round to reasonable number
        final_score = round(final_score, 1)
        
        result.append({
            'career_name': career_name,
            'name': career_name,
            'match_percentage': final_score,
            'match_score': final_score,
            'description': career['description'],
            'salary': career['salary'],
            'required_skills': career['skills'],
            'score_breakdown': {
                'quiz': round(quiz_score * 0.40, 1),
                'personality': round(personality_match * 0.25, 1),
                'skills': round(skills_score * 0.20, 1),
                'academics': round(academics_score * 0.15, 1)
            }
        })
    
    # Sort by match score descending
    result.sort(key=lambda x: x['match_score'], reverse=True)
    
    print(f"   Top career: {result[0]['name']} with {result[0]['match_score']}%")
    
    return result[:5]  # Return top 5

@app.route('/api/assessment/questions/<education_level>')
def get_assessment_questions(education_level):
    """Get assessment questions based on education level."""
    try:
        questions_file = PROJECT_ROOT / 'data' / 'assessment_questions.json'
        with open(questions_file, 'r') as f:
            questions_data = json.load(f)
        
        if education_level not in questions_data['questions']:
            return jsonify({
                'success': False,
                'error': f'Invalid education level: {education_level}'
            }), 400
        
        level_info = questions_data['education_levels'].get(education_level, {})
        questions = questions_data['questions'][education_level]
        time_limit = questions_data['time_limits'].get(education_level, 45)
        
        return jsonify({
            'success': True,
            'education_level': education_level,
            'level_info': level_info,
            'questions': questions,
            'time_limit_minutes': time_limit
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/assessment/submit', methods=['POST'])
def submit_assessment():
    """Submit assessment answers and get career recommendations."""
    print("📥 Assessment submission received")
    data = request.json
    print(f"   Data keys: {data.keys() if data else 'None'}")
    
    user_id = session.get('user_id')
    
    education_level = data.get('education_level', 'undergraduate')
    answers = data.get('answers', {})
    basic_info = data.get('basic_info', {})
    
    print(f"   Education level: {education_level}")
    print(f"   Basic info: {basic_info}")
    print(f"   Answers keys: {answers.keys() if answers else 'None'}")
    
    # Map education level to grade
    grade_mapping = {
        '10th': '10th',
        '12th': '12th',
        'undergraduate': 'Undergraduate',
        'graduate': 'Graduate',
        'postgraduate': 'Post Graduate',
        'working_professional': 'Working Professional',
        'working': 'Working Professional'
    }
    
    # Create student profile for analysis
    try:
        # Extract data from onboarding format
        # The answers object contains: interests, hobbies, academics, skills, personality, domain
        
        # Get interests directly from answers
        interests = answers.get('interests', [])
        if not interests:
            interests = ['Technology', 'Science']  # Default
        print(f"   Interests: {interests}")
        
        # Get skills from answers
        skills = answers.get('skills', {})
        if not skills:
            skills = {'problem_solving': 7, 'communication': 7}
        print(f"   Skills: {skills}")
        
        # Get personality answers
        personality_data = answers.get('personality', {})
        personality_answers = []
        if personality_data:
            for q_id, answer in personality_data.items():
                personality_answers.append({'question': q_id, 'answer': answer})
        print(f"   Personality answers: {len(personality_answers)}")
        
        # Get academic data
        academics = answers.get('academics', [])
        marks_dict = {}
        for subject in academics:
            if isinstance(subject, dict):
                name = subject.get('name', 'Subject')
                marks = subject.get('marks', 70)
                marks_dict[name.lower().replace(' ', '_')] = marks
        print(f"   Academics: {marks_dict}")
        
        # Create a proper StudentProfile
        profile = StudentProfile(
            name=basic_info.get('name', session.get('user_name', 'Student')),
            age=int(basic_info.get('age', 18)),
            grade=grade_mapping.get(education_level, 'Undergraduate'),
            subject_preferences=interests[:5] if interests else ['Technology', 'Science'],
            interests=interests,
            skill_self_ratings=skills if skills else {'problem_solving': 7, 'communication': 7},
            personality_answers=personality_answers,
            family_budget=int(basic_info.get('budget', 500000)),
            budget_currency='INR',
            preferred_locations=basic_info.get('locations', ['India']),
            willing_to_relocate=True,
            marks_10th=marks_dict if education_level in ['10th', '12th', 'undergraduate'] else {},
            marks_12th=marks_dict if education_level in ['12th', 'undergraduate', 'graduate'] else {}
        )
        
        # Add default marks if not provided
        if not profile.marks_10th:
            profile.marks_10th = {'math': 75, 'science': 75, 'english': 70}
        if not profile.marks_12th:
            profile.marks_12th = {'math': 75, 'science': 75, 'english': 70}
        
        print("   🔄 Analyzing student profile...")
        
        # Get specialization and stream from basic_info
        specialization = basic_info.get('specialization', '')
        stream = basic_info.get('stream', '')
        domain_answers = answers.get('domain', {})
        personality_data = answers.get('personality', {})
        skills_data = answers.get('skills', {})
        academics_data = answers.get('academics', [])
        
        print(f"   Specialization: {specialization}, Stream: {stream}")
        print(f"   Domain answers count: {len(domain_answers)}")
        print(f"   Personality answers count: {len(personality_data)}")
        print(f"   Skills count: {len(skills_data)}")
        print(f"   Academics count: {len(academics_data)}")
        
        # Get career recommendations based on specialization with comprehensive scoring
        if specialization or stream:
            # Use specialization-based recommendations with full scoring
            specialization_recommendations = get_careers_for_specialization(
                specialization, 
                stream, 
                domain_answers,
                personality_data,
                skills_data,
                academics_data
            )
            formatted_recommendations = specialization_recommendations
            print(f"   Using specialization-based recommendations: {len(formatted_recommendations)} careers")
        else:
            # Fall back to AI-based analysis
            report = career_system.analyze_student(profile)
            print("   ✅ Analysis complete!")
            
            # Extract recommendations from report
            recommendations = report.get('career_recommendations', [])
            print(f"   Found {len(recommendations)} career recommendations")
            
            # Format recommendations for frontend
            formatted_recommendations = []
            for rec in recommendations:
                career_name = (
                    rec.get('career_name') or 
                    rec.get('name') or 
                    (rec.get('career', {}).get('name') if isinstance(rec.get('career'), dict) else None) or
                    'Career'
                )
                
                description = (
                    rec.get('description') or 
                    (rec.get('career', {}).get('description') if isinstance(rec.get('career'), dict) else None) or
                    'A great career match based on your profile.'
                )
                
                match_score = rec.get('match_percentage') or rec.get('match_score') or rec.get('score') or 85
                
                salary_info = rec.get('salary', {})
                if not salary_info and isinstance(rec.get('career'), dict):
                    salary_range = rec.get('career', {}).get('salary_range', {})
                    salary_info = {
                        'entry': salary_range.get('entry', 600000),
                        'mid': salary_range.get('mid', 1200000),
                        'senior': salary_range.get('senior', 2500000)
                    }
                if not salary_info:
                    salary_info = {'entry': 600000, 'mid': 1200000, 'senior': 2500000}
                
                required_skills = (
                    rec.get('required_skills') or 
                    (rec.get('career', {}).get('required_skills') if isinstance(rec.get('career'), dict) else None) or
                    ['Problem Solving', 'Communication', 'Technical Skills']
                )
                
                formatted_recommendations.append({
                    'career': career_name,
                    'name': career_name,
                    'match_score': match_score,
                    'score': match_score,
                    'description': description,
                    'category': rec.get('category', 'General'),
                    'salary': salary_info,
                    'required_skills': required_skills
                })
        
        # Get personality type
        try:
            report = career_system.analyze_student(profile)
            personality_type = report.get('personality_profile', {}).get('mbti_type', 'INTJ')
        except:
            personality_type = 'INTJ'
        
        print(f"   Formatted {len(formatted_recommendations)} recommendations")
        
        # Save result if user is logged in
        if user_id:
            AssessmentResult.save(
                user_id=user_id,
                assessment_type='comprehensive',
                education_level=education_level,
                answers=answers,
                scores=answers,
                recommendations=formatted_recommendations,
                personality_type=personality_type
            )
        
        response_data = {
            'success': True,
            'recommendations': formatted_recommendations,
            'profile_analysis': {
                'education_level': education_level,
                'specialization': basic_info.get('specialization', ''),
                'stream': basic_info.get('stream', ''),
                'total_questions_answered': len(domain_answers) + len(answers.get('personality', {})),
                'personality_type': personality_type + ' - The Architect'
            }
        }
        
        print("   📤 Sending response")
        return jsonify(response_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============== User Results API ==============

@app.route('/api/user/results')
def get_user_results():
    """Get the latest assessment results for the current user."""
    user_id = session.get('user_id')
    
    if not user_id:
        # No user logged in - return sample data for science stream
        return jsonify({
            'success': True,
            'recommendations': [
                {'career': 'Data Scientist', 'name': 'Data Scientist', 'match_score': 92, 'score': 92, 'description': 'Analyze complex data to uncover insights and drive business decisions using statistical methods and machine learning.', 'salary': {'entry': 900000, 'mid': 1800000, 'senior': 3600000}, 'required_skills': ['Python', 'Machine Learning', 'Statistics', 'SQL']},
                {'career': 'Software Engineer', 'name': 'Software Engineer', 'match_score': 88, 'score': 88, 'description': 'Build innovative software solutions and applications that impact millions of users worldwide.', 'salary': {'entry': 800000, 'mid': 1600000, 'senior': 3200000}, 'required_skills': ['Programming', 'Problem Solving', 'System Design', 'Algorithms']},
                {'career': 'Research Scientist', 'name': 'Research Scientist', 'match_score': 85, 'score': 85, 'description': 'Conduct cutting-edge research to advance scientific knowledge and develop new technologies.', 'salary': {'entry': 700000, 'mid': 1400000, 'senior': 2800000}, 'required_skills': ['Research Methods', 'Data Analysis', 'Scientific Writing', 'Critical Thinking']},
                {'career': 'Machine Learning Engineer', 'name': 'Machine Learning Engineer', 'match_score': 82, 'score': 82, 'description': 'Design and implement machine learning models and AI systems for real-world applications.', 'salary': {'entry': 1000000, 'mid': 2000000, 'senior': 4000000}, 'required_skills': ['Deep Learning', 'TensorFlow/PyTorch', 'Python', 'Mathematics']},
                {'career': 'Biomedical Engineer', 'name': 'Biomedical Engineer', 'match_score': 78, 'score': 78, 'description': 'Apply engineering principles to healthcare, developing medical devices and diagnostic equipment.', 'salary': {'entry': 600000, 'mid': 1200000, 'senior': 2400000}, 'required_skills': ['Biology', 'Engineering', 'Medical Devices', 'Problem Solving']}
            ],
            'profile_analysis': {
                'personality_type': 'INTJ - The Architect',
                'education_level': 'undergraduate'
            }
        })
    
    # Get latest result for user
    result = AssessmentResult.get_latest(user_id)
    
    if result:
        return jsonify({
            'success': True,
            'recommendations': result.get('recommendations', []),
            'profile_analysis': {
                'personality_type': result.get('personality_type', 'INTJ') + ' - The Architect',
                'education_level': result.get('education_level', 'undergraduate')
            }
        })
    
    # No results found - return sample
    return jsonify({
        'success': True,
        'recommendations': [
            {'career': 'Data Scientist', 'name': 'Data Scientist', 'match_score': 92, 'score': 92, 'description': 'Analyze complex data to uncover insights and drive business decisions using statistical methods and machine learning.', 'salary': {'entry': 900000, 'mid': 1800000, 'senior': 3600000}, 'required_skills': ['Python', 'Machine Learning', 'Statistics', 'SQL']},
            {'career': 'Software Engineer', 'name': 'Software Engineer', 'match_score': 88, 'score': 88, 'description': 'Build innovative software solutions and applications that impact millions of users worldwide.', 'salary': {'entry': 800000, 'mid': 1600000, 'senior': 3200000}, 'required_skills': ['Programming', 'Problem Solving', 'System Design', 'Algorithms']},
            {'career': 'Research Scientist', 'name': 'Research Scientist', 'match_score': 85, 'score': 85, 'description': 'Conduct cutting-edge research to advance scientific knowledge and develop new technologies.', 'salary': {'entry': 700000, 'mid': 1400000, 'senior': 2800000}, 'required_skills': ['Research Methods', 'Data Analysis', 'Scientific Writing', 'Critical Thinking']},
            {'career': 'Machine Learning Engineer', 'name': 'Machine Learning Engineer', 'match_score': 82, 'score': 82, 'description': 'Design and implement machine learning models and AI systems for real-world applications.', 'salary': {'entry': 1000000, 'mid': 2000000, 'senior': 4000000}, 'required_skills': ['Deep Learning', 'TensorFlow/PyTorch', 'Python', 'Mathematics']},
            {'career': 'Biomedical Engineer', 'name': 'Biomedical Engineer', 'match_score': 78, 'score': 78, 'description': 'Apply engineering principles to healthcare, developing medical devices and diagnostic equipment.', 'salary': {'entry': 600000, 'mid': 1200000, 'senior': 2400000}, 'required_skills': ['Biology', 'Engineering', 'Medical Devices', 'Problem Solving']}
        ],
        'profile_analysis': {
            'personality_type': 'INTJ - The Architect',
            'education_level': 'undergraduate'
        }
    })


# ============== Error Handlers ==============

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'success': False,
        'error': 'Resource not found'
    }), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============== Main ==============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║           AI CAREER GUIDANCE SYSTEM - Web Server               ║
╠════════════════════════════════════════════════════════════════╣
║  Server running at: http://127.0.0.1:{port}                      ║
║  API Docs: http://127.0.0.1:{port}/api/health                    ║
║  Debug Mode: {debug}                                           ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
