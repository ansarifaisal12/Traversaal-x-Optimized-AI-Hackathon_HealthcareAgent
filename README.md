# HealthGuard AI Healthcare Assistant

A Streamlit-based AI healthcare assistant with Traversaal integration for enhanced medical information retrieval.

## Features

- **Medical Information:** Get reliable medical information backed by Traversaal's medical AI
- **Medication Tracking:** Log and monitor medication intake
- **Symptom Monitoring:** Track symptoms and their severity over time
- **Health Analytics:** View trends and analysis of your health data
- **Multi-patient Support:** Manage separate profiles for different users

## Setup Instructions

1. Clone this repository:
```
git remote add origin https://github.com/ansarifaisal12/Traversaal-x-Optimized-AI-Hackathon_HealthcareAgent.git
cd healthguard
```

2. Install required dependencies:
```
pip install -r requirements.txt
```

3. Configure API keys:
   - Create a `.env` file in the root directory
   - Add the following keys:
```
# Required - Choose one:
OPENAI_API_KEY=your_openai_api_key
# OR
GOOGLE_API_KEY=your_google_api_key

# Optional - For enhanced medical search (recommended):
TRAVERSAAL_ARES_API_KEY=your_traversaal_ares_api_key
```

4. Run the application:
```
streamlit run app.py
```

## Demo Questions

### Medical Information (Using Traversaal)
- "What are the common symptoms of Type 2 diabetes?"
- "Tell me about heart disease prevention strategies"
- "What is hypertension and how is it treated?"
- "Can you explain what asthma is and how it affects breathing?"
- "What are the benefits and risks of statins?"

### Medication Management
- "I took my Lisinopril 10mg this morning"
- "Did I take my Metformin today?"
- "Add a new medication: Atorvastatin 20mg, once daily"
- "What medications am I currently taking?"
- "When was my last dose of aspirin?"

### Symptom Tracking
- "I have a headache, severity 7 out of 10"
- "Track my fatigue level as 3 out of 5 today"
- "My joint pain is better today, about 2 out of 10"
- "What symptoms have I reported in the last week?"
- "Show my headache history"

### Health Analysis
- "Am I taking my medications regularly?"
- "Is there a pattern to my headaches?"
- "Analyze my symptom trends over the past month"
- "How has my joint pain changed over time?"
- "Give me a health summary"

## Project Structure

- `app.py` - Main Streamlit application
- `healthcareagent/` - Core agent and tools
  - `agent.py` - HealthGuard agent implementation
  - `tools/` - Various healthcare tools
    - `medical_info.py` - Traversaal integration for medical information
    - `medication.py` - Medication tracking
    - `symptom.py` - Symptom monitoring
    - `health_analysis.py` - Health analytics
- `data/` - Local database storage

## Technologies

- Streamlit for the frontend
- Traversaal Ares API for enhanced medical information
- Google Gemini or OpenAI for the core AI model
- SQLite for local data storage

## Note

This application is for informational purposes only and should not replace professional medical advice. 
