"""
User Authentication Models
Database models for user management with SQLite
"""

import sqlite3
import hashlib
import secrets
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import json

# Database path
DB_PATH = Path(__file__).parent.parent / 'data' / 'users.db'


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            name TEXT NOT NULL,
            age INTEGER,
            education_level TEXT,
            phone TEXT,
            profile_picture TEXT,
            
            -- OAuth fields
            oauth_provider TEXT,
            oauth_id TEXT,
            
            -- Profile completion
            profile_completed BOOLEAN DEFAULT 0,
            
            -- Timestamps
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sessions table for token management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Assessment results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assessment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            assessment_type TEXT NOT NULL,
            education_level TEXT NOT NULL,
            answers JSON,
            scores JSON,
            career_recommendations JSON,
            personality_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User progress tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            assessment_step INTEGER DEFAULT 0,
            completed_sections JSON,
            saved_answers JSON,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully!")


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, hash_value = stored_hash.split(':')
        return hashlib.sha256((password + salt).encode()).hexdigest() == hash_value
    except:
        return False


class User:
    """User model for authentication and profile management."""
    
    def __init__(self, user_data: dict):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.name = user_data.get('name')
        self.age = user_data.get('age')
        self.education_level = user_data.get('education_level')
        self.phone = user_data.get('phone')
        self.profile_picture = user_data.get('profile_picture')
        self.oauth_provider = user_data.get('oauth_provider')
        self.profile_completed = user_data.get('profile_completed', False)
        self.created_at = user_data.get('created_at')
        self.last_login = user_data.get('last_login')
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'age': self.age,
            'education_level': self.education_level,
            'phone': self.phone,
            'profile_picture': self.profile_picture,
            'oauth_provider': self.oauth_provider,
            'profile_completed': self.profile_completed
        }
    
    @staticmethod
    def create(email: str, password: str, name: str, **kwargs) -> Optional['User']:
        """Create a new user with email/password."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            password_hash = hash_password(password)
            cursor.execute('''
                INSERT INTO users (email, password_hash, name, age, education_level, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                email.lower(),
                password_hash,
                name,
                kwargs.get('age'),
                kwargs.get('education_level'),
                kwargs.get('phone')
            ))
            conn.commit()
            
            user_id = cursor.lastrowid
            return User.get_by_id(user_id)
        except sqlite3.IntegrityError:
            return None  # Email already exists
        finally:
            conn.close()
    
    @staticmethod
    def create_oauth(email: str, name: str, provider: str, oauth_id: str, profile_picture: str = None) -> 'User':
        """Create or get user via OAuth."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists with this OAuth
        cursor.execute('''
            SELECT * FROM users WHERE oauth_provider = ? AND oauth_id = ?
        ''', (provider, oauth_id))
        existing = cursor.fetchone()
        
        if existing:
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP, profile_picture = ?
                WHERE id = ?
            ''', (profile_picture, existing['id']))
            conn.commit()
            conn.close()
            return User(dict(existing))
        
        # Check if email exists (link accounts)
        cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
        email_user = cursor.fetchone()
        
        if email_user:
            # Link OAuth to existing account
            cursor.execute('''
                UPDATE users SET oauth_provider = ?, oauth_id = ?, profile_picture = ?, last_login = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (provider, oauth_id, profile_picture, email_user['id']))
            conn.commit()
            conn.close()
            return User(dict(email_user))
        
        # Create new user
        cursor.execute('''
            INSERT INTO users (email, name, oauth_provider, oauth_id, profile_picture, last_login)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (email.lower(), name, provider, oauth_id, profile_picture))
        conn.commit()
        
        user_id = cursor.lastrowid
        conn.close()
        return User.get_by_id(user_id)
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        """Get user by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return User(dict(row)) if row else None
    
    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        """Get user by email."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
        row = cursor.fetchone()
        conn.close()
        return User(dict(row)) if row else None
    
    @staticmethod
    def authenticate(email: str, password: str) -> Optional['User']:
        """Authenticate user with email/password."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
        row = cursor.fetchone()
        
        if row and row['password_hash'] and verify_password(password, row['password_hash']):
            # Update last login
            cursor.execute('''
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
            ''', (row['id'],))
            conn.commit()
            conn.close()
            return User(dict(row))
        
        conn.close()
        return None
    
    def update_profile(self, **kwargs) -> bool:
        """Update user profile."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        for key in ['name', 'age', 'education_level', 'phone', 'profile_completed']:
            if key in kwargs:
                updates.append(f"{key} = ?")
                values.append(kwargs[key])
        
        if updates:
            values.append(self.id)
            cursor.execute(f'''
                UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', values)
            conn.commit()
        
        conn.close()
        return True


class Session:
    """Session management for user authentication."""
    
    @staticmethod
    def create(user_id: int, days_valid: int = 30) -> str:
        """Create a new session token."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=days_valid)
        
        cursor.execute('''
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES (?, ?, ?)
        ''', (user_id, token, expires_at))
        conn.commit()
        conn.close()
        
        return token
    
    @staticmethod
    def get_user(token: str) -> Optional[User]:
        """Get user from session token."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.* FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at > CURRENT_TIMESTAMP
        ''', (token,))
        row = cursor.fetchone()
        conn.close()
        
        return User(dict(row)) if row else None
    
    @staticmethod
    def delete(token: str) -> bool:
        """Delete session (logout)."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def cleanup_expired():
        """Remove expired sessions."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP')
        conn.commit()
        conn.close()


class AssessmentResult:
    """Store and retrieve assessment results."""
    
    @staticmethod
    def save(user_id: int, assessment_type: str, education_level: str, 
             answers: dict, scores: dict, recommendations: list, personality_type: str = None) -> int:
        """Save assessment result."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assessment_results 
            (user_id, assessment_type, education_level, answers, scores, career_recommendations, personality_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            assessment_type,
            education_level,
            json.dumps(answers),
            json.dumps(scores),
            json.dumps(recommendations),
            personality_type
        ))
        conn.commit()
        result_id = cursor.lastrowid
        conn.close()
        return result_id
    
    @staticmethod
    def get_user_results(user_id: int) -> List[dict]:
        """Get all assessment results for a user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM assessment_results WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            result = dict(row)
            result['answers'] = json.loads(result['answers']) if result['answers'] else {}
            result['scores'] = json.loads(result['scores']) if result['scores'] else {}
            result['career_recommendations'] = json.loads(result['career_recommendations']) if result['career_recommendations'] else []
            results.append(result)
        
        return results
    
    @staticmethod
    def get_latest(user_id: int) -> dict:
        """Get the latest assessment result for a user."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM assessment_results WHERE user_id = ? ORDER BY created_at DESC LIMIT 1
        ''', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        result = dict(row)
        result['answers'] = json.loads(result['answers']) if result['answers'] else {}
        result['scores'] = json.loads(result['scores']) if result['scores'] else {}
        result['recommendations'] = json.loads(result['career_recommendations']) if result['career_recommendations'] else []
        return result


# Initialize database on module import
init_database()
