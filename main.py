"""
AI Career Guidance System - Main Application
Integrates all components for comprehensive career guidance.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.ml_models import (
    SkillPredictionModel,
    PersonalityPredictionModel,
    CareerRecommendationModel,
    SalaryPredictionModel,
    JobMarketTrendAnalyzer,
    ScamContentDetector
)
from utils.data_processor import (
    StudentProfile,
    DataLoader,
    CollegeFinder,
    RoadmapGenerator,
    ReportGenerator
)


class CareerGuidanceSystem:
    """
    Main application class that orchestrates all career guidance components.
    """
    
    def __init__(self, data_dir: str = 'data'):
        """
        Initialize the Career Guidance System.
        
        Args:
            data_dir: Directory containing data files
        """
        self.data_dir = Path(data_dir)
        
        # Initialize data loader
        self.data_loader = DataLoader(data_dir)
        
        # Initialize ML models
        self.skill_model = SkillPredictionModel()
        self.personality_model = PersonalityPredictionModel()
        self.salary_model = SalaryPredictionModel()
        self.job_market_analyzer = JobMarketTrendAnalyzer()
        self.scam_detector = ScamContentDetector()
        
        # Initialize utilities
        self.college_finder = CollegeFinder(self.data_loader)
        self.roadmap_generator = RoadmapGenerator(self.data_loader)
        self.report_generator = ReportGenerator()
        
        # Initialize career recommendation model with data
        careers = self.data_loader.load_careers()
        self.career_model = CareerRecommendationModel(careers)
        
        print("✓ Career Guidance System initialized successfully!")
    
    def analyze_student(self, profile: StudentProfile) -> Dict:
        """
        Perform complete analysis for a student profile.
        
        Args:
            profile: Student profile with all information
        
        Returns:
            Comprehensive analysis results
        """
        print(f"\n📊 Analyzing profile for: {profile.name}")
        
        # 1. Skill Analysis
        print("  → Analyzing skills...")
        subject_scores = profile.get_subject_scores()
        skill_analysis = self.skill_model.predict(subject_scores)
        
        # 2. Personality Analysis
        print("  → Analyzing personality...")
        personality_profile = self.personality_model.get_personality_profile(
            profile.personality_answers
        )
        
        # 3. Career Recommendations
        print("  → Generating career recommendations...")
        user_profile = {
            'skills': skill_analysis,
            'mbti_type': personality_profile['mbti_type'],
            'subjects': profile.subject_preferences,
            'interests': profile.interests
        }
        career_recommendations = self.career_model.recommend(user_profile, top_n=5)
        
        # 4. Top Career Details
        top_career = career_recommendations[0]['career'] if career_recommendations else None
        
        # 5. Salary Predictions
        print("  → Predicting salary trends...")
        salary_predictions = {}
        if top_career:
            salary_predictions = self.salary_model.predict_salary(
                top_career,
                country=profile.budget_currency if profile.budget_currency in ['USD', 'INR', 'EUR'] else 'USD'
            )
        
        # 6. Job Market Forecast
        print("  → Forecasting job market...")
        job_forecast = {}
        if top_career:
            job_forecast = self.job_market_analyzer.forecast_demand(top_career)
        
        # 7. College Recommendations
        print("  → Finding suitable colleges...")
        college_recommendations = []
        if top_career:
            college_recommendations = self.college_finder.find_colleges(
                career_name=top_career['name'],
                budget=profile.family_budget,
                budget_currency=profile.budget_currency,
                preferred_locations=profile.preferred_locations
            )
        
        # 8. Generate Roadmap
        print("  → Creating personalized roadmap...")
        roadmap = {}
        if top_career:
            roadmap = self.roadmap_generator.generate_roadmap(
                career=top_career,
                current_grade=profile.grade,
                current_skills=skill_analysis
            )
        
        # 9. Generate Complete Report
        print("  → Generating final report...")
        report = self.report_generator.generate_report(
            student=profile,
            career_recommendations=career_recommendations,
            personality_profile=personality_profile,
            skill_analysis=skill_analysis,
            college_recommendations=college_recommendations,
            salary_predictions=salary_predictions,
            job_forecast=job_forecast,
            roadmap=roadmap
        )
        
        print("✓ Analysis complete!")
        return report
    
    def get_personality_test(self) -> List[Dict]:
        """Get personality test questions."""
        return self.data_loader.get_personality_questions()
    
    def check_scam_content(self, text: str, source: str = '') -> Dict:
        """
        Check content for potential scam indicators.
        
        Args:
            text: Content to analyze
            source: Source URL or name
        
        Returns:
            Scam analysis results
        """
        return self.scam_detector.analyze_content(text, source)
    
    def get_career_details(self, career_name: str) -> Optional[Dict]:
        """
        Get detailed information about a specific career.
        
        Args:
            career_name: Name of the career
        
        Returns:
            Career details or None
        """
        careers = self.data_loader.load_careers()
        for career in careers:
            if career['name'].lower() == career_name.lower():
                return {
                    'career': career,
                    'salary_projection': self.salary_model.predict_salary(career),
                    'job_forecast': self.job_market_analyzer.forecast_demand(career)
                }
        return None
    
    def compare_careers(self, career_names: List[str]) -> List[Dict]:
        """
        Compare multiple careers side by side.
        
        Args:
            career_names: List of career names to compare
        
        Returns:
            Comparison data for each career
        """
        comparisons = []
        for name in career_names:
            details = self.get_career_details(name)
            if details:
                comparisons.append(details)
        return comparisons
    
    def get_all_careers(self) -> List[Dict]:
        """Get list of all available careers."""
        return self.data_loader.load_careers()
    
    def get_mbti_info(self, mbti_type: str) -> Optional[Dict]:
        """Get information about an MBTI personality type."""
        return self.data_loader.get_mbti_info(mbti_type)


def create_sample_profile() -> StudentProfile:
    """Create a sample student profile for testing."""
    return StudentProfile(
        name="Test Student",
        age=17,
        grade="12th",
        marks_10th={
            'mathematics': 85,
            'science': 88,
            'english': 78,
            'social_science': 75,
            'computer': 92
        },
        marks_12th={
            'mathematics': 82,
            'physics': 85,
            'chemistry': 78,
            'computer_science': 90,
            'english': 80
        },
        subject_preferences=['Computer Science', 'Mathematics', 'Physics'],
        interests=['Technology', 'Programming', 'Gaming', 'Problem Solving'],
        skill_self_ratings={
            'programming': 8,
            'mathematics': 7,
            'communication': 6,
            'creativity': 7,
            'leadership': 5
        },
        personality_answers=[
            {'scores': {'E': 0, 'I': 2}},  # Introvert
            {'scores': {'T': 2, 'F': 0}},  # Thinking
            {'scores': {'J': 1, 'P': 1}},  # Balanced
            {'scores': {'S': 0, 'N': 2}},  # Intuitive
            {'scores': {'openness': 1}},
            {'scores': {'conscientiousness': 2}}
        ],
        family_budget=500000,
        budget_currency='INR',
        preferred_locations=['India', 'USA'],
        willing_to_relocate=True
    )


def print_report_summary(report: Dict):
    """Print a formatted summary of the career guidance report."""
    print("\n" + "=" * 70)
    print("📋 CAREER GUIDANCE REPORT")
    print("=" * 70)
    
    # Student Info
    student = report.get('student_info', {})
    print(f"\n👤 Student: {student.get('name', 'Unknown')}")
    print(f"   Age: {student.get('age', 'N/A')} | Grade: {student.get('grade', 'N/A')}")
    print(f"   Average Marks: {student.get('average_marks', 'N/A')}%")
    
    # Personality
    personality = report.get('personality_analysis', {})
    print(f"\n🧠 Personality Type: {personality.get('mbti_type', 'Unknown')}")
    if personality.get('key_strengths'):
        print("   Key Strengths:", ", ".join(personality['key_strengths']))
    
    # Skills
    skills = report.get('skill_analysis', {})
    if skills.get('top_skills'):
        print(f"\n💪 Top Skills:")
        for skill in skills['top_skills']:
            print(f"   • {skill}")
    
    # Career Recommendations
    print(f"\n🎯 TOP CAREER RECOMMENDATIONS:")
    print("-" * 50)
    for rec in report.get('career_recommendations', [])[:5]:
        print(f"\n   #{rec['rank']} {rec['career_name']}")
        print(f"      Match: {rec['match_percentage']}% | Category: {rec['category']}")
        print(f"      Difficulty: {rec['difficulty_level']}/10 | Automation Risk: {rec['automation_risk']}")
        print(f"      Description: {rec['description'][:80]}...")
    
    # Salary Projections
    salary = report.get('salary_projections', {})
    if salary:
        print(f"\n💰 SALARY PROJECTIONS (Top Career):")
        print(f"   Starting: {salary.get('starting', 'N/A'):,}")
        print(f"   After 5 years: {salary.get('5_years', 'N/A'):,}")
        print(f"   After 10 years: {salary.get('10_years', 'N/A'):,}")
        print(f"   Annual Growth: {salary.get('growth_rate', 'N/A')}")
    
    # Job Market
    market = report.get('job_market_outlook', {})
    if market:
        print(f"\n📈 JOB MARKET OUTLOOK:")
        print(f"   10-Year Outlook: {market.get('10_year_outlook', 'Unknown')}")
        print(f"   Growth Rate: {market.get('growth_rate', 'N/A')}")
        print(f"   AI Impact: {market.get('ai_impact', 'Unknown')}")
    
    # College Recommendations
    print(f"\n🎓 TOP COLLEGE RECOMMENDATIONS:")
    for col in report.get('college_recommendations', [])[:3]:
        print(f"   #{col['rank']} {col['name']}")
        print(f"      Location: {col['location']} | Score: {col['suitability_score']}%")
        print(f"      Fees: {col['fees']:,} | Placement: {col['placement_rate']}")
    
    # Next Steps
    print(f"\n📝 RECOMMENDED NEXT STEPS:")
    for i, step in enumerate(report.get('next_steps', []), 1):
        print(f"   {i}. {step}")
    
    print("\n" + "=" * 70)


def main():
    """Main function to demonstrate the Career Guidance System."""
    print("\n🚀 Starting AI Career Guidance System...")
    print("=" * 70)
    
    # Initialize the system
    system = CareerGuidanceSystem()
    
    # Create a sample profile
    print("\n📝 Creating sample student profile...")
    profile = create_sample_profile()
    
    # Analyze the student
    report = system.analyze_student(profile)
    
    # Print the report
    print_report_summary(report)
    
    # Test scam detector
    print("\n🔍 Testing Scam Content Detector:")
    print("-" * 50)
    
    scam_texts = [
        "Learn Python and earn 5 lakh per month guaranteed! No experience needed!",
        "Google Data Analytics Professional Certificate - Learn data analysis skills",
        "Secret method to become a millionaire in 30 days! Limited spots available!"
    ]
    
    for text in scam_texts:
        result = system.check_scam_content(text)
        print(f"\nText: '{text[:50]}...'")
        print(f"Verdict: {result['verdict']}")
        print(f"Scam Probability: {result['scam_probability']}%")
    
    # Save report to file
    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)
    
    report_path = output_dir / 'sample_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Full report saved to: {report_path}")
    print("\n🎉 Demo complete!")


if __name__ == "__main__":
    main()
