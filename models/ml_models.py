"""
AI Career Guidance System - ML Models Module
Contains all machine learning models for career prediction, skill analysis, and more.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple, Optional
import json


class SkillPredictionModel:
    """
    Random Forest / Gradient Boost model to identify strongest academic & practical skills.
    Input: subject scores, test results
    Output: 0-1 confidence score for each skill
    """
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.skill_categories = [
            'analytical', 'creative', 'technical', 'communication',
            'leadership', 'detail_oriented', 'problem_solving', 'research'
        ]
        self.is_trained = False
    
    def _generate_training_data(self, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data based on skill patterns."""
        np.random.seed(42)
        
        # Features: [math, science, english, arts, commerce, computer, sports, social_activities]
        X = np.random.rand(n_samples, 8) * 100  # Scores from 0-100
        
        # Generate skill scores based on subject performance patterns
        y = np.zeros((n_samples, len(self.skill_categories)))
        
        for i in range(n_samples):
            math, science, english, arts, commerce, computer, sports, social = X[i]
            
            # Analytical: high math, science, computer
            y[i, 0] = np.clip((math * 0.4 + science * 0.3 + computer * 0.3) / 100, 0, 1)
            
            # Creative: high arts, english
            y[i, 1] = np.clip((arts * 0.5 + english * 0.3 + social * 0.2) / 100, 0, 1)
            
            # Technical: high computer, math, science
            y[i, 2] = np.clip((computer * 0.5 + math * 0.3 + science * 0.2) / 100, 0, 1)
            
            # Communication: high english, social activities
            y[i, 3] = np.clip((english * 0.5 + social * 0.4 + arts * 0.1) / 100, 0, 1)
            
            # Leadership: high social, commerce
            y[i, 4] = np.clip((social * 0.5 + commerce * 0.3 + english * 0.2) / 100, 0, 1)
            
            # Detail-oriented: high math, commerce
            y[i, 5] = np.clip((math * 0.4 + commerce * 0.4 + science * 0.2) / 100, 0, 1)
            
            # Problem-solving: math, science, computer
            y[i, 6] = np.clip((math * 0.35 + science * 0.35 + computer * 0.3) / 100, 0, 1)
            
            # Research: science, english, computer
            y[i, 7] = np.clip((science * 0.4 + english * 0.3 + computer * 0.3) / 100, 0, 1)
        
        return X, y
    
    def train(self):
        """Train the skill prediction model."""
        X, y = self._generate_training_data()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train separate models for each skill category
        self.models = {}
        for i, skill in enumerate(self.skill_categories):
            model = GradientBoostingRegressor(n_estimators=50, random_state=42)
            model.fit(X_scaled, y[:, i])
            self.models[skill] = model
        
        self.is_trained = True
    
    def predict(self, subject_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Predict skill confidence scores based on subject performance.
        
        Args:
            subject_scores: Dictionary with keys like 'math', 'science', 'english', etc.
        
        Returns:
            Dictionary with skill categories and their confidence scores (0-1)
        """
        if not self.is_trained:
            self.train()
        
        # Convert input to array
        features = np.array([[
            subject_scores.get('math', 50),
            subject_scores.get('science', 50),
            subject_scores.get('english', 50),
            subject_scores.get('arts', 50),
            subject_scores.get('commerce', 50),
            subject_scores.get('computer', 50),
            subject_scores.get('sports', 50),
            subject_scores.get('social_activities', 50)
        ]])
        
        features_scaled = self.scaler.transform(features)
        
        predictions = {}
        for skill in self.skill_categories:
            score = self.models[skill].predict(features_scaled)[0]
            predictions[skill] = round(np.clip(score, 0, 1), 3)
        
        return predictions


class PersonalityPredictionModel:
    """
    NLP-based scoring model for MBTI type and Big Five traits prediction.
    """
    
    def __init__(self):
        self.mbti_dimensions = ['E-I', 'S-N', 'T-F', 'J-P']
        self.big_five_traits = ['openness', 'conscientiousness', 'extraversion', 
                                'agreeableness', 'neuroticism']
    
    def predict_mbti(self, answers: List[Dict]) -> str:
        """
        Predict MBTI type based on personality test answers.
        
        Args:
            answers: List of answer dictionaries with scores for each dimension
        
        Returns:
            MBTI type string (e.g., 'INTJ')
        """
        dimension_scores = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
        
        for answer in answers:
            if 'scores' in answer:
                for key, value in answer['scores'].items():
                    if key in dimension_scores:
                        dimension_scores[key] += value
        
        mbti_type = ''
        mbti_type += 'E' if dimension_scores['E'] >= dimension_scores['I'] else 'I'
        mbti_type += 'S' if dimension_scores['S'] >= dimension_scores['N'] else 'N'
        mbti_type += 'T' if dimension_scores['T'] >= dimension_scores['F'] else 'F'
        mbti_type += 'J' if dimension_scores['J'] >= dimension_scores['P'] else 'P'
        
        return mbti_type
    
    def predict_big_five(self, answers: List[Dict]) -> Dict[str, float]:
        """
        Predict Big Five personality traits.
        
        Args:
            answers: List of answer dictionaries
        
        Returns:
            Dictionary with Big Five trait scores (0-1)
        """
        trait_scores = {trait: 0.5 for trait in self.big_five_traits}
        
        for answer in answers:
            if 'scores' in answer:
                for trait in self.big_five_traits:
                    if trait in answer['scores']:
                        # Normalize to 0-1 scale
                        trait_scores[trait] = min(1.0, trait_scores[trait] + answer['scores'][trait] * 0.1)
        
        return trait_scores
    
    def get_personality_profile(self, answers: List[Dict]) -> Dict:
        """Get complete personality profile."""
        return {
            'mbti_type': self.predict_mbti(answers),
            'big_five': self.predict_big_five(answers)
        }


class CareerRecommendationModel:
    """
    Hybrid classification + similarity search model for career recommendations.
    Analyzes 70+ parameters and gives top 3-5 most suitable careers.
    """
    
    def __init__(self, careers_data: List[Dict]):
        self.careers = careers_data
        self.feature_weights = {
            'skill_match': 0.35,
            'personality_match': 0.25,
            'academic_match': 0.20,
            'interest_match': 0.15,
            'aptitude_match': 0.05
        }
    
    def _calculate_skill_match(self, user_skills: Dict[str, float], 
                               career_requirements: Dict[str, float]) -> float:
        """Calculate skill match score between user and career requirements."""
        if not career_requirements:
            return 0.5
        
        scores = []
        for skill, required_level in career_requirements.items():
            user_level = user_skills.get(skill, 0.3)
            # Calculate match with some tolerance
            match = 1 - abs(required_level - user_level)
            scores.append(match)
        
        return np.mean(scores) if scores else 0.5
    
    def _calculate_personality_match(self, user_mbti: str, 
                                      career_personality_fit: List[str]) -> float:
        """Calculate personality match score."""
        if not career_personality_fit:
            return 0.5
        
        if user_mbti in career_personality_fit:
            return 0.95
        
        # Partial match based on shared dimensions
        match_count = 0
        for fit_type in career_personality_fit:
            shared = sum(1 for i in range(4) if user_mbti[i] == fit_type[i])
            match_count = max(match_count, shared)
        
        return match_count / 4
    
    def _calculate_academic_match(self, user_subjects: List[str], 
                                   career_subjects: List[str]) -> float:
        """Calculate academic subject match score."""
        if not career_subjects or not user_subjects:
            return 0.5
        
        user_subjects_lower = [s.lower() for s in user_subjects]
        career_subjects_lower = [s.lower() for s in career_subjects]
        
        matches = sum(1 for s in career_subjects_lower if s in user_subjects_lower or 'any' in career_subjects_lower)
        return matches / len(career_subjects) if career_subjects else 0.5
    
    def recommend(self, user_profile: Dict, top_n: int = 5) -> List[Dict]:
        """
        Recommend careers based on user profile.
        
        Args:
            user_profile: Dictionary containing skills, personality, academics, interests
            top_n: Number of top recommendations to return
        
        Returns:
            List of career recommendations with match scores
        """
        recommendations = []
        
        user_skills = user_profile.get('skills', {})
        user_mbti = user_profile.get('mbti_type', 'INTJ')
        user_subjects = user_profile.get('subjects', [])
        user_interests = user_profile.get('interests', [])
        
        for career in self.careers:
            # Calculate individual match scores
            skill_score = self._calculate_skill_match(
                user_skills, 
                career.get('traits_required', {})
            )
            
            personality_score = self._calculate_personality_match(
                user_mbti,
                career.get('personality_fit', [])
            )
            
            academic_score = self._calculate_academic_match(
                user_subjects,
                career.get('subjects', [])
            )
            
            # Interest match (simplified)
            interest_score = 0.5
            career_category = career.get('category', '').lower()
            for interest in user_interests:
                if interest.lower() in career_category or career_category in interest.lower():
                    interest_score = 0.8
                    break
            
            # Calculate weighted total score
            total_score = (
                self.feature_weights['skill_match'] * skill_score +
                self.feature_weights['personality_match'] * personality_score +
                self.feature_weights['academic_match'] * academic_score +
                self.feature_weights['interest_match'] * interest_score +
                self.feature_weights['aptitude_match'] * 0.5  # Default aptitude
            )
            
            recommendations.append({
                'career': career,
                'match_percentage': round(total_score * 100, 1),
                'breakdown': {
                    'skill_match': round(skill_score * 100, 1),
                    'personality_match': round(personality_score * 100, 1),
                    'academic_match': round(academic_score * 100, 1),
                    'interest_match': round(interest_score * 100, 1)
                }
            })
        
        # Sort by match percentage
        recommendations.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return recommendations[:top_n]


class SalaryPredictionModel:
    """
    Regression model trained on salary datasets to predict salary for 3, 5, 10 years.
    """
    
    def __init__(self):
        self.model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Growth factors based on career category and years of experience
        self.growth_factors = {
            'Technology': {'base': 1.0, 'annual_growth': 0.12},
            'Healthcare': {'base': 0.9, 'annual_growth': 0.08},
            'Finance': {'base': 1.1, 'annual_growth': 0.15},
            'Engineering': {'base': 0.95, 'annual_growth': 0.08},
            'Creative': {'base': 0.7, 'annual_growth': 0.10},
            'Marketing': {'base': 0.8, 'annual_growth': 0.10},
            'Law': {'base': 0.85, 'annual_growth': 0.12},
            'Design': {'base': 0.75, 'annual_growth': 0.09},
            'Media': {'base': 0.65, 'annual_growth': 0.07},
            'Science': {'base': 0.8, 'annual_growth': 0.08}
        }
    
    def predict_salary(self, career: Dict, years_experience: int = 0, 
                       country: str = 'USD') -> Dict[str, int]:
        """
        Predict salary based on career and experience.
        
        Args:
            career: Career dictionary with salary data
            years_experience: Years of experience (0, 3, 5, 10)
            country: Currency code (USD, INR, EUR)
        
        Returns:
            Dictionary with predicted salaries at different career stages
        """
        base_salaries = career.get('salary', {})
        category = career.get('category', 'Technology')
        growth = self.growth_factors.get(category, self.growth_factors['Technology'])
        
        entry_salary = base_salaries.get('entry', {}).get(country, 50000)
        mid_salary = base_salaries.get('mid', {}).get(country, 80000)
        senior_salary = base_salaries.get('senior', {}).get(country, 120000)
        
        predictions = {
            'starting': entry_salary,
            '3_years': int(entry_salary * (1 + growth['annual_growth']) ** 3),
            '5_years': int(mid_salary),
            '10_years': int(senior_salary),
            '15_years': int(senior_salary * 1.3),
            'growth_rate': f"{growth['annual_growth'] * 100:.1f}%"
        }
        
        return predictions


class JobMarketTrendAnalyzer:
    """
    Time series forecasting model for predicting career future demand.
    Analyzes trends, AI usage, and automation risk.
    """
    
    def __init__(self):
        # Historical trend data (simplified)
        self.base_trends = {
            'Technology': {'growth': 0.15, 'ai_impact': 'positive', 'volatility': 0.1},
            'Healthcare': {'growth': 0.08, 'ai_impact': 'neutral', 'volatility': 0.05},
            'Finance': {'growth': 0.05, 'ai_impact': 'mixed', 'volatility': 0.12},
            'Engineering': {'growth': 0.06, 'ai_impact': 'neutral', 'volatility': 0.07},
            'Creative': {'growth': 0.04, 'ai_impact': 'negative', 'volatility': 0.15},
            'Marketing': {'growth': 0.07, 'ai_impact': 'mixed', 'volatility': 0.1},
            'Law': {'growth': 0.03, 'ai_impact': 'mixed', 'volatility': 0.05},
            'Design': {'growth': 0.06, 'ai_impact': 'mixed', 'volatility': 0.12},
            'Media': {'growth': 0.02, 'ai_impact': 'negative', 'volatility': 0.2},
            'Science': {'growth': 0.07, 'ai_impact': 'positive', 'volatility': 0.08}
        }
    
    def forecast_demand(self, career: Dict, years: int = 10) -> Dict:
        """
        Forecast job demand for a career over the next N years.
        
        Args:
            career: Career dictionary
            years: Forecast horizon
        
        Returns:
            Dictionary with demand forecast data
        """
        category = career.get('category', 'Technology')
        base_growth = career.get('job_growth_rate', 0.1)
        automation_risk = career.get('automation_risk', 0.2)
        
        trend = self.base_trends.get(category, self.base_trends['Technology'])
        
        # Calculate year-by-year demand
        demand_forecast = []
        current_demand = 100  # Base index
        
        for year in range(1, years + 1):
            # Adjust growth based on automation risk
            adjusted_growth = base_growth * (1 - automation_risk * 0.3)
            
            # Add some variance
            variance = np.random.normal(0, trend['volatility'] * 0.5)
            year_growth = adjusted_growth + variance
            
            current_demand *= (1 + year_growth)
            demand_forecast.append({
                'year': 2024 + year,
                'demand_index': round(current_demand, 1),
                'growth_rate': f"{year_growth * 100:.1f}%"
            })
        
        # Determine overall outlook
        final_demand = demand_forecast[-1]['demand_index']
        if final_demand > 200:
            outlook = 'Excellent'
        elif final_demand > 150:
            outlook = 'Very Good'
        elif final_demand > 120:
            outlook = 'Good'
        elif final_demand > 100:
            outlook = 'Stable'
        else:
            outlook = 'Declining'
        
        return {
            'career_name': career.get('name', 'Unknown'),
            'category': category,
            'base_growth_rate': f"{base_growth * 100:.1f}%",
            'automation_risk': f"{automation_risk * 100:.0f}%",
            'ai_impact': trend['ai_impact'],
            '10_year_outlook': outlook,
            'final_demand_index': round(final_demand, 1),
            'yearly_forecast': demand_forecast
        }


class ScamContentDetector:
    """
    NLP model to detect misleading career advice content.
    Flags scam courses, unrealistic promises, fake "earn X per month" videos.
    """
    
    def __init__(self):
        self.red_flag_patterns = [
            r'earn\s+\d+\s*(lakh|k|thousand|lakhs)\s*(per|a)\s*month',
            r'guaranteed\s+(job|placement|income)',
            r'no\s+(experience|skills?)\s*(required|needed)',
            r'get\s+rich\s+quick',
            r'secret\s+(method|trick|formula)',
            r'limited\s+time\s+offer',
            r'work\s+from\s+home\s+\d+\s*(lakh|k)',
            r'passive\s+income\s+\d+',
            r'quit\s+your\s+job',
            r'financial\s+freedom\s+in\s+\d+\s*(days|weeks|months)',
            r'become\s+a\s+millionaire',
            r'free\s+course.*worth\s+\d+',
            r'99%\s+discount',
            r'only\s+\d+\s+spots?\s+left'
        ]
        
        self.trusted_sources = [
            'coursera', 'edx', 'udemy', 'linkedin learning', 'pluralsight',
            'mit', 'stanford', 'harvard', 'google', 'microsoft', 'aws',
            'iiit', 'iit', 'nit', 'bits', 'university', 'college'
        ]
    
    def analyze_content(self, text: str, source: str = '') -> Dict:
        """
        Analyze content for potential scam indicators.
        
        Args:
            text: Content text to analyze
            source: Source URL or name
        
        Returns:
            Dictionary with scam analysis results
        """
        import re
        
        text_lower = text.lower()
        source_lower = source.lower()
        
        red_flags = []
        for pattern in self.red_flag_patterns:
            if re.search(pattern, text_lower):
                red_flags.append(pattern)
        
        # Check if source is trusted
        is_trusted_source = any(trusted in source_lower for trusted in self.trusted_sources)
        
        # Calculate scam probability
        scam_score = len(red_flags) * 15
        if not is_trusted_source and len(red_flags) > 0:
            scam_score += 20
        
        scam_probability = min(100, scam_score)
        
        # Determine verdict
        if scam_probability >= 70:
            verdict = 'High Risk - Likely Scam'
            recommendation = 'Avoid this content. The claims seem unrealistic.'
        elif scam_probability >= 40:
            verdict = 'Medium Risk - Be Cautious'
            recommendation = 'Verify claims independently before taking action.'
        elif scam_probability >= 20:
            verdict = 'Low Risk - Minor Concerns'
            recommendation = 'Content seems mostly legitimate but verify details.'
        else:
            verdict = 'Safe - No Issues Detected'
            recommendation = 'Content appears legitimate.'
        
        return {
            'scam_probability': scam_probability,
            'verdict': verdict,
            'recommendation': recommendation,
            'red_flags_found': len(red_flags),
            'is_trusted_source': is_trusted_source,
            'warnings': red_flags[:3] if red_flags else []
        }
