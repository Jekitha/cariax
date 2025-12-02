# 🎯 AI Career Guidance System

A comprehensive AI-powered career guidance platform that helps students discover their ideal career paths through advanced machine learning, personality analysis, and real-time AI mentoring.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![AI](https://img.shields.io/badge/AI-Powered-purple.svg)

## ✨ Features

### 1. 🧠 AI Skill Detection
- Analyzes your existing skills
- Identifies skill gaps for desired careers
- Recommends learning paths

### 2. 📊 Academic Performance Analyzer
- Evaluates academic scores
- Maps subjects to career aptitude
- Considers competitive exam performance

### 3. 🎭 Personality & Interest Profiler
- MBTI personality assessment
- Big Five personality traits analysis
- Career-personality matching

### 4. 🎯 Career Match Engine
- ML-powered career recommendations
- Compatibility scoring (0-100%)
- Multiple career path suggestions

### 5. 🗺️ AI Roadmap Generator
- Personalized step-by-step career plans
- Timeline-based milestones
- Skill development priorities

### 6. 💰 Future Salary Predictor
- 10-year salary projections
- Location-based adjustments
- Experience-level forecasting

### 7. 📈 Job Market Demand Predictor
- 10-year job demand forecast
- AI/Automation impact analysis
- Industry growth predictions

### 8. 🎓 College & Courses Finder
- Top college recommendations
- Course matching
- Scholarship information

### 9. 🚨 Fake Career Trap Detector
- Scam job identification
- MLM scheme warnings
- Red flag detection

### 10. 🤖 AI Mentor Chatbot
- 24/7 career counseling
- Personalized advice
- Real-time Q&A support

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- GitHub Personal Access Token (for AI features)

### Installation

1. **Clone/Navigate to the project directory:**
   ```bash
   cd career
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy the example file
   copy .env.example .env
   
   # Edit .env and add your GitHub token
   # GITHUB_TOKEN=your_github_personal_access_token
   ```

5. **Get a GitHub Token:**
   - Go to https://github.com/settings/tokens
   - Generate a new token (classic)
   - Select scopes: `read:user` (minimum)
   - Copy the token to your `.env` file

### Running the Application

#### Web Interface (Recommended)
```bash
python web/app.py
```
Then open http://localhost:5000 in your browser.

#### Command Line Interface
```bash
python main.py
```

## 📁 Project Structure

```
career/
├── data/
│   ├── careers.json         # 120+ career paths database
│   ├── colleges.json         # College recommendations
│   ├── skills.json           # Skills taxonomy
│   └── personality_data.json # MBTI & Big Five data
├── models/
│   ├── __init__.py
│   └── ml_models.py          # ML prediction models
├── utils/
│   ├── __init__.py
│   └── data_processor.py     # Data processing utilities
├── chatbot/
│   ├── __init__.py
│   └── mentor_chatbot.py     # AI Mentor implementation
├── web/
│   ├── app.py                # Flask web application
│   └── templates/
│       ├── index.html        # Landing page
│       ├── assessment.html   # Career assessment form
│       ├── results.html      # Career report page
│       ├── careers.html      # Career explorer
│       └── chat.html         # AI Mentor chat interface
├── main.py                   # CLI application
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITHUB_TOKEN` | GitHub Personal Access Token for AI features | Yes |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | No (auto-generated) |
| `DEBUG` | Enable debug mode (True/False) | No |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Landing page |
| `/assessment` | GET | Career assessment form |
| `/results` | GET | Career report page |
| `/careers` | GET | Career explorer |
| `/chat` | GET | AI Mentor chat interface |
| `/api/analyze` | POST | Analyze student profile |
| `/api/chat` | POST | Chat with AI Mentor |
| `/api/careers` | GET | List all careers |
| `/api/careers/<name>` | GET | Get career details |
| `/api/colleges` | GET | Get college recommendations |

## 🧪 ML Models

### 1. SkillPredictionModel
- **Algorithm:** Random Forest Classifier
- **Purpose:** Predict skill levels and gaps

### 2. PersonalityPredictionModel
- **Algorithm:** Random Forest Classifier
- **Purpose:** MBTI type prediction from traits

### 3. CareerRecommendationModel
- **Algorithm:** Cosine Similarity + Content-Based Filtering
- **Purpose:** Match students to careers

### 4. SalaryPredictionModel
- **Algorithm:** Gradient Boosting Regressor
- **Purpose:** Predict future salary

### 5. JobMarketTrendModel
- **Algorithm:** Time Series Analysis
- **Purpose:** Forecast job market demand

### 6. ScamContentDetector
- **Algorithm:** TF-IDF + Keyword Analysis
- **Purpose:** Detect fraudulent job postings

## 🤖 AI Integration

The system uses **GitHub Models** for AI-powered features:

- **Model:** GPT-4.1-mini (via GitHub Models API)
- **Endpoint:** https://models.github.ai/inference
- **Features:**
  - Career counseling conversations
  - Personalized advice generation
  - Real-time Q&A support

## 📊 Data Sources

- **Careers:** 20+ detailed career profiles with salary ranges, skills, growth rates
- **Colleges:** Top Indian & International institutions
- **Skills:** Comprehensive skill taxonomy across domains
- **Personality:** MBTI & Big Five frameworks

## 🛠️ Development

### Adding New Careers
Edit `data/careers.json`:
```json
{
  "id": 21,
  "name": "New Career",
  "category": "Category",
  "description": "Description...",
  "required_skills": ["skill1", "skill2"],
  "salary_range": {"min": 50000, "max": 150000},
  ...
}
```

### Adding New Colleges
Edit `data/colleges.json`:
```json
{
  "id": 21,
  "name": "College Name",
  "location": "City, Country",
  "ranking": "National/Global ranking",
  ...
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Error: agent_framework**
   - The system falls back to SimpleChatbot if agent_framework is unavailable
   - Ensure you have the latest version: `pip install agent-framework-azure-ai --pre`

2. **GitHub API Rate Limit**
   - Use a valid GitHub token
   - The free tier allows 60 requests/hour without token, 5000 with token

3. **Model Loading Issues**
   - Models are trained on first run
   - Ensure all data files exist in the `data/` directory

## 📝 License

This project is for educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📧 Support

For questions or support, use the AI Mentor chatbot or create an issue.

---

**Built with ❤️ using Python, Flask, and AI**
