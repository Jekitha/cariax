"""
Data Processing Utilities for AI Career Guidance System
Handles loading, validation, and transformation of all data sources.
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StudentProfile:
    """Data class representing a student's complete profile."""
    name: str
    age: int
    grade: str
    
    # Academic Performance
    marks_10th: Dict[str, float] = field(default_factory=dict)
    marks_12th: Dict[str, float] = field(default_factory=dict)
    
    # Preferences
    subject_preferences: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    
    # Self-ratings (0-10 scale)
    skill_self_ratings: Dict[str, int] = field(default_factory=dict)
    
    # Personality test answers
    personality_answers: List[Dict] = field(default_factory=list)
    
    # Financial
    family_budget: int = 0  # Annual budget for college
    budget_currency: str = 'INR'
    
    # Location preference
    preferred_locations: List[str] = field(default_factory=list)
    willing_to_relocate: bool = True
    
    # Timestamp
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_average_marks(self) -> float:
        """Calculate average marks across all subjects."""
        all_marks = list(self.marks_10th.values()) + list(self.marks_12th.values())
        return sum(all_marks) / len(all_marks) if all_marks else 0
    
    def get_subject_scores(self) -> Dict[str, float]:
        """Get normalized subject scores for ML models."""
        scores = {}
        
        # Map common subject names
        subject_mapping = {
            'mathematics': 'math', 'maths': 'math', 'math': 'math',
            'physics': 'science', 'chemistry': 'science', 'biology': 'science', 'science': 'science',
            'english': 'english', 'hindi': 'english', 'language': 'english',
            'arts': 'arts', 'art': 'arts', 'fine arts': 'arts', 'drawing': 'arts',
            'commerce': 'commerce', 'accountancy': 'commerce', 'economics': 'commerce', 'business': 'commerce',
            'computer': 'computer', 'computer science': 'computer', 'it': 'computer', 'programming': 'computer',
            'physical education': 'sports', 'sports': 'sports', 'pe': 'sports',
            'social science': 'social_activities', 'social': 'social_activities', 'history': 'social_activities'
        }
        
        all_marks = {**self.marks_10th, **self.marks_12th}
        
        for subject, mark in all_marks.items():
            subject_key = subject_mapping.get(subject.lower(), 'other')
            if subject_key in scores:
                scores[subject_key] = (scores[subject_key] + mark) / 2
            else:
                scores[subject_key] = mark
        
        # Fill in defaults for missing subjects
        default_subjects = ['math', 'science', 'english', 'arts', 'commerce', 'computer', 'sports', 'social_activities']
        for subj in default_subjects:
            if subj not in scores:
                scores[subj] = 50  # Default score
        
        return scores
    
    def to_dict(self) -> Dict:
        """Convert profile to dictionary."""
        return {
            'name': self.name,
            'age': self.age,
            'grade': self.grade,
            'marks_10th': self.marks_10th,
            'marks_12th': self.marks_12th,
            'subject_preferences': self.subject_preferences,
            'interests': self.interests,
            'skill_self_ratings': self.skill_self_ratings,
            'personality_answers': self.personality_answers,
            'family_budget': self.family_budget,
            'budget_currency': self.budget_currency,
            'preferred_locations': self.preferred_locations,
            'willing_to_relocate': self.willing_to_relocate,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StudentProfile':
        """Create profile from dictionary."""
        return cls(
            name=data.get('name', ''),
            age=data.get('age', 0),
            grade=data.get('grade', ''),
            marks_10th=data.get('marks_10th', {}),
            marks_12th=data.get('marks_12th', {}),
            subject_preferences=data.get('subject_preferences', []),
            interests=data.get('interests', []),
            skill_self_ratings=data.get('skill_self_ratings', {}),
            personality_answers=data.get('personality_answers', []),
            family_budget=data.get('family_budget', 0),
            budget_currency=data.get('budget_currency', 'INR'),
            preferred_locations=data.get('preferred_locations', []),
            willing_to_relocate=data.get('willing_to_relocate', True),
            created_at=data.get('created_at', datetime.now().isoformat())
        )


class DataLoader:
    """Handles loading and caching of all data files."""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = Path(data_dir)
        self._cache = {}
    
    def _load_json(self, filename: str) -> Dict:
        """Load JSON file with caching."""
        if filename in self._cache:
            return self._cache[filename]
        
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._cache[filename] = data
        return data
    
    def load_careers(self) -> List[Dict]:
        """Load careers data."""
        data = self._load_json('careers.json')
        return data.get('careers', [])
    
    def load_colleges(self) -> List[Dict]:
        """Load colleges data."""
        data = self._load_json('colleges.json')
        return data.get('colleges', [])
    
    def load_skills(self) -> Dict:
        """Load skills data."""
        return self._load_json('skills.json')
    
    def load_personality_data(self) -> Dict:
        """Load personality and MBTI data."""
        return self._load_json('personality_data.json')
    
    def get_personality_questions(self) -> List[Dict]:
        """Get personality test questions."""
        data = self.load_personality_data()
        return data.get('personality_questions', [])
    
    def get_mbti_info(self, mbti_type: str) -> Optional[Dict]:
        """Get information about a specific MBTI type."""
        data = self.load_personality_data()
        return data.get('mbti_types', {}).get(mbti_type)
    
    def get_online_courses(self, skills: List[str] = None) -> List[Dict]:
        """Get online course recommendations."""
        data = self.load_skills()
        courses = data.get('online_courses', [])
        
        if skills:
            skills_lower = [s.lower() for s in skills]
            filtered = []
            for course in courses:
                course_skills = [s.lower() for s in course.get('skills', [])]
                if any(s in course_skills for s in skills_lower):
                    filtered.append(course)
            return filtered
        
        return courses
    
    def clear_cache(self):
        """Clear the data cache."""
        self._cache = {}


class CollegeFinder:
    """
    Module to find and recommend colleges based on student profile.
    Considers budget, location, cutoff, and course quality.
    """
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
    
    def find_colleges(self, 
                      career_name: str,
                      budget: int,
                      budget_currency: str = 'INR',
                      preferred_locations: List[str] = None,
                      min_ranking: int = None) -> List[Dict]:
        """
        Find suitable colleges for a career path.
        
        Args:
            career_name: Target career
            budget: Annual budget
            budget_currency: Currency code
            preferred_locations: List of preferred locations/countries
            min_ranking: Minimum acceptable ranking
        
        Returns:
            List of matching colleges with suitability scores
        """
        colleges = self.data_loader.load_colleges()
        
        # Map careers to relevant courses
        career_course_mapping = {
            'data scientist': ['Computer Science', 'Data Science', 'AI/ML', 'Statistics'],
            'software engineer': ['Computer Science', 'Engineering', 'IT'],
            'ai/ml engineer': ['Computer Science', 'AI/ML', 'Data Science'],
            'medical doctor': ['MBBS', 'Medicine', 'MD'],
            'chartered accountant': ['Commerce', 'Accounting', 'MBA'],
            'graphic designer': ['Design', 'Graphic Design', 'Fine Arts'],
            'civil engineer': ['Civil Engineering', 'Engineering'],
            'mechanical engineer': ['Mechanical Engineering', 'Engineering'],
            'digital marketing': ['Marketing', 'MBA', 'Business'],
            'psychologist': ['Psychology', 'Counseling'],
            'lawyer': ['Law', 'LLB', 'LLM'],
            'architect': ['Architecture'],
            'product manager': ['MBA', 'Management', 'Computer Science'],
            'ux designer': ['Design', 'UX Design', 'HCI'],
            'fashion designer': ['Fashion Design', 'Design']
        }
        
        relevant_courses = career_course_mapping.get(
            career_name.lower(), 
            ['Computer Science', 'Engineering', 'MBA']
        )
        
        matching_colleges = []
        
        for college in colleges:
            # Check if college offers relevant courses
            college_courses = college.get('courses', [])
            course_match = any(
                any(rc.lower() in cc.lower() or cc.lower() in rc.lower() 
                    for cc in college_courses) 
                for rc in relevant_courses
            )
            
            if not course_match:
                continue
            
            # Check budget
            fees = college.get('fees_per_year', {}).get(budget_currency, float('inf'))
            if fees > budget:
                budget_fit = 'over_budget'
                budget_score = 0.3
            elif fees < budget * 0.5:
                budget_fit = 'well_within_budget'
                budget_score = 1.0
            else:
                budget_fit = 'within_budget'
                budget_score = 0.8
            
            # Check location preference
            college_location = college.get('location', '')
            college_country = college.get('country', '')
            location_score = 0.5
            
            if preferred_locations:
                for loc in preferred_locations:
                    if loc.lower() in college_location.lower() or loc.lower() in college_country.lower():
                        location_score = 1.0
                        break
            else:
                location_score = 0.7
            
            # Calculate ranking score
            ranking = college.get('ranking', 100)
            ranking_score = max(0, 1 - (ranking - 1) / 50)
            
            # Placement score
            placement_rate = college.get('placement_rate', 0.5)
            
            # Calculate overall suitability
            suitability = (
                budget_score * 0.25 +
                location_score * 0.20 +
                ranking_score * 0.25 +
                placement_rate * 0.30
            )
            
            matching_colleges.append({
                'college': college,
                'suitability_score': round(suitability * 100, 1),
                'budget_fit': budget_fit,
                'fees': fees,
                'ranking': ranking,
                'placement_rate': f"{placement_rate * 100:.0f}%"
            })
        
        # Sort by suitability
        matching_colleges.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return matching_colleges


class RoadmapGenerator:
    """
    Generates personalized learning roadmap for the next 5 years.
    """
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
    
    def generate_roadmap(self, 
                         career: Dict, 
                         current_grade: str,
                         current_skills: Dict[str, float]) -> Dict:
        """
        Generate a 5-year personalized roadmap.
        
        Args:
            career: Target career dictionary
            current_grade: Student's current grade
            current_skills: Current skill levels
        
        Returns:
            Dictionary with year-by-year roadmap
        """
        required_skills = career.get('required_skills', [])
        difficulty = career.get('difficulty', 5)
        course_duration = career.get('course_duration_years', 4)
        
        roadmap = {
            'career_goal': career.get('name'),
            'total_duration': '5 years',
            'phases': []
        }
        
        # Year 1: Foundation
        roadmap['phases'].append({
            'year': 1,
            'title': 'Foundation Building',
            'goals': [
                'Complete current education with focus on relevant subjects',
                f'Begin learning basics of: {", ".join(required_skills[:2])}',
                'Explore career through online resources and videos',
                'Join relevant online communities and forums'
            ],
            'skills_to_develop': required_skills[:2],
            'recommended_courses': self._get_beginner_courses(required_skills[:2]),
            'milestones': [
                'Complete 2 online courses',
                'Build 1-2 small projects',
                'Attend 1 career webinar'
            ]
        })
        
        # Year 2: Skill Development
        roadmap['phases'].append({
            'year': 2,
            'title': 'Core Skill Development',
            'goals': [
                f'Master fundamentals of: {", ".join(required_skills[1:3])}',
                'Start building portfolio projects',
                'Participate in competitions/hackathons',
                'Get mentorship or guidance'
            ],
            'skills_to_develop': required_skills[1:4],
            'recommended_courses': self._get_intermediate_courses(required_skills[1:4]),
            'milestones': [
                'Complete 3-4 intermediate courses',
                'Build 3-5 portfolio projects',
                'Participate in 1-2 competitions'
            ]
        })
        
        # Year 3: Specialization
        roadmap['phases'].append({
            'year': 3,
            'title': 'Specialization & Practical Experience',
            'goals': [
                f'Specialize in: {required_skills[0] if required_skills else "core domain"}',
                'Apply for internships',
                'Contribute to open-source/real projects',
                'Build professional network'
            ],
            'skills_to_develop': required_skills[2:5] if len(required_skills) > 2 else required_skills,
            'recommended_courses': self._get_advanced_courses(career.get('category', 'Technology')),
            'milestones': [
                'Complete 1-2 certifications',
                'Get internship experience',
                'Build 2-3 advanced projects'
            ]
        })
        
        # Year 4: Professional Preparation
        roadmap['phases'].append({
            'year': 4,
            'title': 'Professional Preparation',
            'goals': [
                'Complete degree/certification requirements',
                'Gain practical work experience',
                'Prepare for job interviews',
                'Build strong online presence'
            ],
            'skills_to_develop': ['Interview Skills', 'Professional Communication', 'Industry Tools'],
            'recommended_courses': ['Interview Preparation', 'Resume Building', 'LinkedIn Optimization'],
            'milestones': [
                'Complete education',
                'Have 2-3 internship experiences',
                'Apply for entry-level positions'
            ]
        })
        
        # Year 5: Career Launch
        roadmap['phases'].append({
            'year': 5,
            'title': 'Career Launch & Growth',
            'goals': [
                'Secure full-time position',
                'Continue learning advanced topics',
                'Establish expertise in chosen domain',
                'Plan for career advancement'
            ],
            'skills_to_develop': ['Leadership', 'Advanced Domain Knowledge', 'Soft Skills'],
            'recommended_courses': ['Leadership Development', 'Advanced Specialization'],
            'milestones': [
                'Get first full-time job',
                'Complete 1 year in role',
                'Get first promotion or significant project'
            ]
        })
        
        return roadmap
    
    def _get_beginner_courses(self, skills: List[str]) -> List[str]:
        """Get beginner-level course recommendations."""
        courses_map = {
            'programming': ['CS50 by Harvard', 'Python for Everybody (Coursera)'],
            'python': ['Python for Everybody', 'Automate the Boring Stuff'],
            'data': ['Google Data Analytics Certificate'],
            'machine learning': ['ML Crash Course by Google'],
            'design': ['Google UX Design Certificate'],
            'communication': ['Business Communication (LinkedIn Learning)'],
            'default': ['Career Foundations Course', 'Basic Skills Development']
        }
        
        recommendations = []
        for skill in skills:
            skill_lower = skill.lower()
            for key, courses in courses_map.items():
                if key in skill_lower:
                    recommendations.extend(courses)
                    break
            else:
                recommendations.extend(courses_map['default'])
        
        return list(set(recommendations))[:4]
    
    def _get_intermediate_courses(self, skills: List[str]) -> List[str]:
        """Get intermediate-level course recommendations."""
        return [
            'Intermediate Specialization Courses',
            'Industry-Specific Certifications',
            'Project-Based Learning Programs'
        ]
    
    def _get_advanced_courses(self, category: str) -> List[str]:
        """Get advanced-level course recommendations."""
        category_courses = {
            'Technology': ['AWS/Azure Certification', 'Advanced Programming'],
            'Healthcare': ['Medical Specialization', 'Research Methods'],
            'Finance': ['CFA Preparation', 'Financial Modeling'],
            'Creative': ['Portfolio Development', 'Industry Software Mastery'],
            'default': ['Advanced Professional Certification', 'Leadership Course']
        }
        
        return category_courses.get(category, category_courses['default'])


class ReportGenerator:
    """
    Generates comprehensive career guidance reports.
    """
    
    def __init__(self):
        pass
    
    def generate_report(self, 
                        student: StudentProfile,
                        career_recommendations: List[Dict],
                        personality_profile: Dict,
                        skill_analysis: Dict,
                        college_recommendations: List[Dict],
                        salary_predictions: Dict,
                        job_forecast: Dict,
                        roadmap: Dict) -> Dict:
        """
        Generate a comprehensive career guidance report.
        
        Returns:
            Complete report dictionary
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'student_info': {
                'name': student.name,
                'age': student.age,
                'grade': student.grade,
                'average_marks': round(student.get_average_marks(), 1)
            },
            'personality_analysis': {
                'mbti_type': personality_profile.get('mbti_type', 'Unknown'),
                'big_five_traits': personality_profile.get('big_five', {}),
                'key_strengths': self._get_key_strengths(personality_profile)
            },
            'skill_analysis': {
                'top_skills': self._get_top_skills(skill_analysis),
                'areas_for_improvement': self._get_improvement_areas(skill_analysis),
                'detailed_scores': skill_analysis
            },
            'career_recommendations': [
                {
                    'rank': i + 1,
                    'career_name': rec['career']['name'],
                    'match_percentage': rec['match_percentage'],
                    'category': rec['career'].get('category', 'Unknown'),
                    'description': rec['career'].get('description', ''),
                    'difficulty_level': rec['career'].get('difficulty', 5),
                    'automation_risk': f"{rec['career'].get('automation_risk', 0) * 100:.0f}%",
                    'required_skills': rec['career'].get('required_skills', []),
                    'education_required': rec['career'].get('education', ''),
                    'match_breakdown': rec.get('breakdown', {})
                }
                for i, rec in enumerate(career_recommendations[:5])
            ],
            'salary_projections': salary_predictions,
            'job_market_outlook': {
                '10_year_outlook': job_forecast.get('10_year_outlook', 'Unknown'),
                'growth_rate': job_forecast.get('base_growth_rate', 'N/A'),
                'automation_risk': job_forecast.get('automation_risk', 'N/A'),
                'ai_impact': job_forecast.get('ai_impact', 'Unknown')
            },
            'college_recommendations': [
                {
                    'rank': i + 1,
                    'name': col['college']['name'],
                    'location': col['college'].get('location', ''),
                    'suitability_score': col['suitability_score'],
                    'fees': col['fees'],
                    'placement_rate': col['placement_rate'],
                    'scholarships': col['college'].get('scholarships', [])
                }
                for i, col in enumerate(college_recommendations[:5])
            ],
            '5_year_roadmap': roadmap,
            'next_steps': self._generate_next_steps(career_recommendations, student)
        }
        
        return report
    
    def _get_key_strengths(self, personality: Dict) -> List[str]:
        """Extract key strengths from personality profile."""
        strengths = []
        big_five = personality.get('big_five', {})
        
        if big_five.get('openness', 0) > 0.7:
            strengths.append('Creative and imaginative')
        if big_five.get('conscientiousness', 0) > 0.7:
            strengths.append('Organized and dependable')
        if big_five.get('extraversion', 0) > 0.7:
            strengths.append('Sociable and assertive')
        if big_five.get('agreeableness', 0) > 0.7:
            strengths.append('Cooperative and empathetic')
        
        return strengths if strengths else ['Balanced personality traits']
    
    def _get_top_skills(self, skills: Dict) -> List[str]:
        """Get top 3 skills."""
        sorted_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)
        return [f"{skill.replace('_', ' ').title()}: {score:.0%}" 
                for skill, score in sorted_skills[:3]]
    
    def _get_improvement_areas(self, skills: Dict) -> List[str]:
        """Get areas that need improvement."""
        sorted_skills = sorted(skills.items(), key=lambda x: x[1])
        return [f"{skill.replace('_', ' ').title()}" 
                for skill, score in sorted_skills[:2] if score < 0.5]
    
    def _generate_next_steps(self, recommendations: List[Dict], student: StudentProfile) -> List[str]:
        """Generate actionable next steps."""
        if not recommendations:
            return ['Take the full assessment to get personalized recommendations']
        
        top_career = recommendations[0]['career']
        
        return [
            f"Research more about {top_career['name']} career path",
            f"Start learning: {top_career.get('required_skills', ['foundational skills'])[0]}",
            "Take online courses relevant to your top career match",
            "Connect with professionals in your field of interest",
            "Build a portfolio with small projects"
        ]
