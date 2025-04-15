import json
import sqlite3
import os
import datetime
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging

from .base import LLMHealthTool

logger = logging.getLogger(__name__)

# SQL commands for medication database
CREATE_MEDICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    frequency TEXT NOT NULL,
    time_of_day TEXT,
    notes TEXT,
    start_date TEXT,
    end_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

CREATE_MEDICATION_LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS medication_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    taken_at TEXT NOT NULL,
    taken BOOLEAN NOT NULL,
    notes TEXT,
    FOREIGN KEY (medication_id) REFERENCES medications (id)
);
"""


class MedicationTool(LLMHealthTool):
    """
    Tool for managing patient medications, schedules, and adherence tracking.
    """
    name: str = "Medication Tool"
    description: str = "tracks and manages patient medications, schedules, and reminders"
    arg: str = "JSON object with medication information or query"
    db_path: Optional[str] = None
    
    def __init__(self, **data):
        """Initialize the medication tool and database."""
        super().__init__(**data)
        
        # Set up database connection with absolute path
        if self.db_path is None:
            # Get the current directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # Create data directory if it doesn't exist
            data_dir = os.path.join(current_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            # Set absolute path to database
            self.db_path = os.path.join(data_dir, "medications.db")
            logger.info(f"Using absolute database path: {self.db_path}")
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the medication database schema and add sample data if empty."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Create tables if they don't exist
                cursor.execute(CREATE_MEDICATIONS_TABLE)
                cursor.execute(CREATE_MEDICATION_LOGS_TABLE)
                conn.commit()
                logger.info(f"Medication database tables ensured at {self.db_path}")

                # Check if medications table is empty for the demo patient
                cursor.execute("SELECT COUNT(*) FROM medications WHERE patient_id = ?", ('demo_patient_001',))
                count = cursor.fetchone()[0]

                if count == 0:
                    logger.info("Medications table empty for demo patient. Adding sample data...")
                    now = datetime.datetime.now().isoformat()
                    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()
                    two_days_ago = (datetime.datetime.now() - datetime.timedelta(days=2)).isoformat()

                    # Add sample medications
                    sample_meds = [
                        ('demo_patient_001', 'Lisinopril', '10mg', 'Once daily', 'Morning', 'For blood pressure', yesterday, '', now, now),
                        ('demo_patient_001', 'Metformin', '500mg', 'Twice daily', 'Morning, Evening', 'For blood sugar', two_days_ago, '', now, now),
                        ('demo_patient_001', 'Vitamin D', '1000 IU', 'Once daily', 'Anytime', None, yesterday, '', now, now)
                    ]
                    cursor.executemany("""
                        INSERT INTO medications 
                        (patient_id, name, dosage, frequency, time_of_day, notes, start_date, end_date, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, sample_meds)
                    
                    # Get IDs of inserted meds for logs
                    cursor.execute("SELECT id FROM medications WHERE patient_id = ?", ('demo_patient_001',))
                    med_ids = [row[0] for row in cursor.fetchall()]
                    
                    if len(med_ids) >= 2:
                        lisinopril_id = med_ids[0]
                        metformin_id = med_ids[1]

                        # Add sample logs
                        sample_logs = [
                            (lisinopril_id, yesterday, True, 'Taken with breakfast'),
                            (metformin_id, two_days_ago, True, 'Taken morning dose'),
                            (metformin_id, yesterday, False, 'Forgot evening dose'),
                            (lisinopril_id, now, True, 'Taken morning dose')
                        ]
                        cursor.executemany("""
                            INSERT INTO medication_logs (medication_id, taken_at, taken, notes)
                            VALUES (?, ?, ?, ?)
                        """, sample_logs)

                    conn.commit()
                    logger.info("Sample medication data added for patient 'demo_patient_001'.")
                else:
                    logger.info("Medication data already exists for demo patient.")

        except Exception as e:
            logger.error(f"Error initializing medication database or adding sample data: {str(e)}")
            raise
    
    def run(self, prompt: Union[str, Dict]) -> str:
        """
        Process medication-related requests.
        
        Args:
            prompt: String query or structured dictionary with medication data
            
        Returns:
            Response with medication information or confirmation
        """
        # If prompt is a string, attempt to parse for intent
        if isinstance(prompt, str):
            return self._process_text_prompt(prompt)
        
        # If prompt is a dictionary, process structured request
        elif isinstance(prompt, dict):
            action = prompt.get("action", "").lower()
            
            if action == "add":
                return self._add_medication(prompt)
            elif action == "list":
                return self._list_medications(prompt.get("patient_id", "default"))
            elif action == "update":
                return self._update_medication(prompt)
            elif action == "log":
                return self._log_medication_taken(prompt)
            elif action == "adherence":
                return self._get_adherence(prompt.get("patient_id", "default"))
            else:
                return f"Unknown action: {action}. Supported actions are: add, list, update, log, adherence."
        
        # Handle invalid input
        else:
            return "Invalid input format. Please provide either a text query or a properly structured medication object."
    
    def _process_text_prompt(self, prompt: str) -> str:
        """Process a natural language medication-related query."""
        # Use LLM to parse the intent and extract structured data
        system_prompt = """
        You are a medication management assistant. Parse the user's request into a structured format.
        Extract the following information if present:
        - Action (add, list, update, log, or adherence)
        - Medication name
        - Dosage
        - Frequency (e.g., daily, twice daily, etc.)
        - Time of day
        - Any other relevant details
        
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
            return "I couldn't parse your medication request. Please provide more specific details about what you'd like to do with your medications."
    
    def _add_medication(self, data: Dict) -> str:
        """Add a new medication to the database."""
        required_fields = ["patient_id", "name", "dosage", "frequency"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        # Standardize time format
        now = datetime.datetime.now().isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO medications 
                    (patient_id, name, dosage, frequency, time_of_day, notes, 
                     start_date, end_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data.get("patient_id", "default"),
                        data["name"],
                        data["dosage"],
                        data["frequency"],
                        data.get("time_of_day", ""),
                        data.get("notes", ""),
                        data.get("start_date", now),
                        data.get("end_date", ""),
                        now,
                        now
                    )
                )
                medication_id = cursor.lastrowid
                conn.commit()
                
                return f"Added medication: {data['name']} ({data['dosage']}) to be taken {data['frequency']}. Medication ID: {medication_id}"
        except Exception as e:
            logger.error(f"Error adding medication: {str(e)}")
            return f"Error adding medication: {str(e)}"
    
    def _list_medications(self, patient_id: str) -> str:
        """List all medications for a patient."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM medications WHERE patient_id = ? ORDER BY name",
                    (patient_id,)
                )
                
                medications = cursor.fetchall()
                
                if not medications:
                    return f"No medications found for patient ID: {patient_id}"
                
                result = f"Medications for patient {patient_id}:\n\n"
                for med in medications:
                    result += f"- {med['name']} ({med['dosage']})\n"
                    result += f"  Frequency: {med['frequency']}\n"
                    if med['time_of_day']:
                        result += f"  Time: {med['time_of_day']}\n"
                    if med['notes']:
                        result += f"  Notes: {med['notes']}\n"
                    result += "\n"
                
                return result
        except Exception as e:
            logger.error(f"Error listing medications: {str(e)}")
            return f"Error listing medications: {str(e)}"
    
    def _update_medication(self, data: Dict) -> str:
        """Update an existing medication."""
        if "id" not in data:
            return "Missing medication ID for update"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if medication exists
                cursor.execute("SELECT id FROM medications WHERE id = ?", (data["id"],))
                if cursor.fetchone() is None:
                    return f"Medication with ID {data['id']} not found"
                
                # Build update query dynamically based on provided fields
                update_fields = []
                update_values = []
                
                field_mapping = {
                    "name": "name", 
                    "dosage": "dosage", 
                    "frequency": "frequency",
                    "time_of_day": "time_of_day", 
                    "notes": "notes", 
                    "start_date": "start_date",
                    "end_date": "end_date"
                }
                
                for key, db_field in field_mapping.items():
                    if key in data:
                        update_fields.append(f"{db_field} = ?")
                        update_values.append(data[key])
                
                # Add updated_at timestamp
                update_fields.append("updated_at = ?")
                update_values.append(datetime.datetime.now().isoformat())
                
                # Add medication ID for WHERE clause
                update_values.append(data["id"])
                
                # Execute update
                cursor.execute(
                    f"UPDATE medications SET {', '.join(update_fields)} WHERE id = ?",
                    update_values
                )
                conn.commit()
                
                return f"Updated medication ID {data['id']}"
        except Exception as e:
            logger.error(f"Error updating medication: {str(e)}")
            return f"Error updating medication: {str(e)}"
    
    def _log_medication_taken(self, data: Dict) -> str:
        """Log whether a medication was taken."""
        required_fields = ["medication_id", "taken"]
        for field in required_fields:
            if field not in data:
                return f"Missing required field: {field}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if medication exists
                cursor.execute("SELECT id FROM medications WHERE id = ?", (data["medication_id"],))
                if cursor.fetchone() is None:
                    return f"Medication with ID {data['medication_id']} not found"
                
                # Log medication taken status
                cursor.execute(
                    """
                    INSERT INTO medication_logs 
                    (medication_id, taken_at, taken, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        data["medication_id"],
                        data.get("taken_at", datetime.datetime.now().isoformat()),
                        bool(data["taken"]),
                        data.get("notes", "")
                    )
                )
                conn.commit()
                
                status = "taken" if data["taken"] else "skipped"
                return f"Logged medication ID {data['medication_id']} as {status}"
        except Exception as e:
            logger.error(f"Error logging medication: {str(e)}")
            return f"Error logging medication: {str(e)}"
    
    def _get_adherence(self, patient_id: str) -> str:
        """Calculate medication adherence statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all medications for the patient
                cursor.execute(
                    "SELECT id, name FROM medications WHERE patient_id = ?",
                    (patient_id,)
                )
                medications = cursor.fetchall()
                
                if not medications:
                    return f"No medications found for patient ID: {patient_id}"
                
                result = f"Medication Adherence Report for patient {patient_id}:\n\n"
                
                for med in medications:
                    # Get logs for this medication
                    cursor.execute(
                        """
                        SELECT COUNT(*) as total, 
                               SUM(CASE WHEN taken = 1 THEN 1 ELSE 0 END) as taken
                        FROM medication_logs
                        WHERE medication_id = ?
                        """,
                        (med["id"],)
                    )
                    stats = cursor.fetchone()
                    
                    if stats["total"] == 0:
                        adherence = "No data"
                    else:
                        adherence_rate = (stats["taken"] / stats["total"]) * 100
                        adherence = f"{adherence_rate:.1f}% ({stats['taken']}/{stats['total']})"
                    
                    result += f"- {med['name']}: {adherence}\n"
                
                return result
        except Exception as e:
            logger.error(f"Error calculating adherence: {str(e)}")
            return f"Error calculating adherence: {str(e)}" 