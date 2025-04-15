import json
import sqlite3
import os
import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging

from .base import LLMHealthTool

logger = logging.getLogger(__name__)

# SQL commands for symptom database
CREATE_SYMPTOMS_TABLE = """
CREATE TABLE IF NOT EXISTS symptoms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    symptom TEXT NOT NULL,
    severity INTEGER NOT NULL,
    description TEXT,
    date_recorded TEXT NOT NULL,
    duration TEXT,
    triggers TEXT,
    created_at TEXT NOT NULL
);
"""

class SymptomTool(LLMHealthTool):
    """
    Tool for tracking and analyzing patient symptoms.
    """
    name: str = "Symptom Tool"
    description: str = "logs and analyzes patient symptoms, tracks patterns, and provides insights"
    arg: str = "JSON object with symptom information or query"
    db_path: Optional[str] = None
    
    def __init__(self, **data):
        """Initialize the symptom tool and database."""
        super().__init__(**data)
        
        # Set up database connection with absolute path
        if self.db_path is None:
            # Get the current directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # Create data directory if it doesn't exist
            data_dir = os.path.join(current_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            # Set absolute path to database
            self.db_path = os.path.join(data_dir, "symptoms.db")
            logger.info(f"Using absolute database path: {self.db_path}")
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the symptom database schema and add sample data if empty."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Create table if it doesn't exist
                cursor.execute(CREATE_SYMPTOMS_TABLE)
                conn.commit()
                logger.info(f"Symptom database table ensured at {self.db_path}")

                # Check if symptoms table is empty for the demo patient
                cursor.execute("SELECT COUNT(*) FROM symptoms WHERE patient_id = ?", ('demo_patient_001',))
                count = cursor.fetchone()[0]

                if count == 0:
                    logger.info("Symptoms table empty for demo patient. Adding sample data...")
                    now = datetime.datetime.now()
                    yesterday = (now - datetime.timedelta(days=1)).isoformat()
                    two_days_ago = (now - datetime.timedelta(days=2)).isoformat()
                    now_iso = now.isoformat()

                    # Add sample symptoms
                    sample_symptoms = [
                        ('demo_patient_001', 'Headache', 6, 'Pressure behind eyes', two_days_ago, '2 hours', 'Stress', two_days_ago),
                        ('demo_patient_001', 'Fatigue', 7, 'Feeling sluggish all day', yesterday, 'All day', 'Poor sleep', yesterday),
                        ('demo_patient_001', 'Headache', 4, 'Mild throbbing', now_iso, 'Ongoing', 'Screen time', now_iso)
                    ]
                    cursor.executemany("""
                        INSERT INTO symptoms 
                        (patient_id, symptom, severity, description, date_recorded, duration, triggers, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, sample_symptoms)
                    
                    conn.commit()
                    logger.info("Sample symptom data added for patient 'demo_patient_001'.")
                else:
                    logger.info("Symptom data already exists for demo patient.")

        except Exception as e:
            logger.error(f"Error initializing symptom database or adding sample data: {str(e)}")
            raise
    
    def run(self, prompt: Union[str, Dict]) -> str:
        """
        Process symptom-related requests.
        
        Args:
            prompt: String query or structured dictionary with symptom data
            
        Returns:
            Response with symptom information or confirmation
        """
        # Handle string input by using LLM to parse
        if isinstance(prompt, str):
            return self._process_text_prompt(prompt)
        
        # Handle structured dictionary input
        elif isinstance(prompt, dict):
            action = prompt.get("action", "").lower()
            
            if action == "log":
                return self._log_symptom(prompt)
            elif action == "list":
                return self._list_symptoms(prompt.get("patient_id", "default"))
            elif action == "analyze":
                return self._analyze_symptoms(prompt.get("patient_id", "default"))
            else:
                return f"Unknown action: {action}. Supported actions are: log, list, analyze."
        
        # Handle invalid input
        else:
            return "Invalid input format. Please provide either a text query or a properly structured symptom object."
    
    def _process_text_prompt(self, prompt: str) -> str:
        """Process a natural language symptom-related query."""
        system_prompt = """
        You are a symptom tracking assistant. Parse the user's request into a structured format.
        Extract the following information if present:
        - Action (log, list, analyze)
        - Symptom name
        - Severity (1-10 or descriptions like mild, moderate, severe)
        - Description of the symptom
        - When it started or duration
        - Any possible triggers
        
        Return a JSON object with the extracted information.
        """
        
        try:
            # Get structured data from LLM
            llm_response = self.get_llm_response(prompt, system_prompt)
            parsed_data = json.loads(llm_response)
            
            # Process the structured data
            return self.run(parsed_data)
        except json.JSONDecodeError:
            # If parsing fails, handle as a general query
            return "I couldn't parse your symptom request. Please provide more specific details about what you'd like to do with your symptom tracking."
    
    def _log_symptom(self, data: Dict) -> str:
        """Log a new symptom entry."""
        required_fields = ["patient_id", "symptom", "severity"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        # Convert severity descriptions to numeric values if needed
        severity = data["severity"]
        if isinstance(severity, str):
            severity_map = {
                "mild": 3, "light": 3, "minor": 2, "minimal": 1, "slight": 2,
                "moderate": 5, "medium": 5, "average": 5,
                "severe": 8, "intense": 8, "extreme": 10, "worst": 10, "serious": 9,
                "very mild": 2, "very severe": 9
            }
            
            # Try to map the string to a numeric value, default to 5 if unknown
            severity = severity_map.get(severity.lower(), 5)
        
        # Ensure severity is within range 1-10
        try:
            severity = int(severity)
            severity = max(1, min(10, severity))
        except (ValueError, TypeError):
            severity = 5  # Default to moderate if conversion fails
        
        # Standardize time format
        now = datetime.datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO symptoms 
                    (patient_id, symptom, severity, description, date_recorded, duration, triggers, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data.get("patient_id", "default"),
                        data["symptom"],
                        severity,
                        data.get("description", ""),
                        data.get("date_recorded", now),
                        data.get("duration", ""),
                        data.get("triggers", ""),
                        now
                    )
                )
                conn.commit()
                
                severity_desc = {
                    1: "very mild", 2: "mild", 3: "mild to moderate", 
                    4: "moderate", 5: "moderate", 6: "moderate to severe",
                    7: "severe", 8: "severe", 9: "very severe", 10: "extreme"
                }
                
                return f"Logged {severity_desc.get(severity, '')} {data['symptom']} symptom."
        except Exception as e:
            logger.error(f"Error logging symptom: {str(e)}")
            return f"Error logging symptom: {str(e)}"
    
    def _list_symptoms(self, patient_id: str) -> str:
        """List all symptoms for a patient."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT symptom, severity, date_recorded, description, duration, triggers
                    FROM symptoms
                    WHERE patient_id = ?
                    ORDER BY date_recorded DESC
                    """,
                    (patient_id,)
                )
                
                symptoms = cursor.fetchall()
                
                if not symptoms:
                    return f"No symptoms recorded for patient ID: {patient_id}"
                
                result = f"Recent symptoms for patient {patient_id}:\n\n"
                for symptom in symptoms:
                    date = datetime.datetime.fromisoformat(symptom["date_recorded"]).strftime("%Y-%m-%d %H:%M")
                    result += f"- {symptom['symptom']} (Severity: {symptom['severity']}/10) on {date}\n"
                    if symptom["description"]:
                        result += f"  Description: {symptom['description']}\n"
                    if symptom["duration"]:
                        result += f"  Duration: {symptom['duration']}\n"
                    if symptom["triggers"]:
                        result += f"  Possible triggers: {symptom['triggers']}\n"
                    result += "\n"
                
                return result
        except Exception as e:
            logger.error(f"Error listing symptoms: {str(e)}")
            return f"Error listing symptoms: {str(e)}"
    
    def _analyze_symptoms(self, patient_id: str) -> str:
        """Analyze symptoms to identify patterns and provide insights."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all symptoms for patient
                cursor.execute(
                    """
                    SELECT symptom, severity, date_recorded, triggers
                    FROM symptoms
                    WHERE patient_id = ?
                    ORDER BY date_recorded
                    """,
                    (patient_id,)
                )
                
                symptoms = cursor.fetchall()
                
                if not symptoms:
                    return f"No symptoms recorded for patient ID: {patient_id}. Unable to perform analysis."
                
                # Convert to list of dicts for easier processing
                symptom_data = []
                for s in symptoms:
                    symptom_data.append({
                        "symptom": s["symptom"],
                        "severity": s["severity"],
                        "date": s["date_recorded"],
                        "triggers": s["triggers"]
                    })
                
                # Use LLM to analyze the symptoms
                analysis_prompt = f"""
                Analyze the following symptom data for a patient:
                
                {json.dumps(symptom_data, indent=2)}
                
                Identify:
                1. Any patterns in symptom occurrence
                2. Potential triggers
                3. Progression of severity over time
                4. Correlations between different symptoms (if present)
                5. Suggestions for lifestyle adjustments that might help (no medical advice)
                
                Keep your analysis concise and focus on the patterns in the data.
                """
                
                analysis = self.get_llm_response(analysis_prompt)
                return f"Symptom Analysis for patient {patient_id}:\n\n{analysis}"
                
        except Exception as e:
            logger.error(f"Error analyzing symptoms: {str(e)}")
            return f"Error analyzing symptoms: {str(e)}" 