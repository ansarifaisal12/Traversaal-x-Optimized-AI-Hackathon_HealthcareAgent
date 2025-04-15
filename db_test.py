import os
import sqlite3
import json

# Get absolute path to data directory
current_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(current_dir, "data")
os.makedirs(data_dir, exist_ok=True)

# Database paths
medications_db = os.path.join(data_dir, "medications.db")
symptoms_db = os.path.join(data_dir, "symptoms.db")

print(f"Current directory: {current_dir}")
print(f"Data directory: {data_dir}")
print(f"Medication database path: {medications_db}")
print(f"Symptom database path: {symptoms_db}")

# Test medication database
try:
    print("\nTesting medication database...")
    conn = sqlite3.connect(medications_db)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        name TEXT NOT NULL,
        dosage TEXT NOT NULL,
        frequency TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    print("Medication database created successfully")
    conn.close()
except Exception as e:
    print(f"Error with medication database: {str(e)}")

# Test symptom database
try:
    print("\nTesting symptom database...")
    conn = sqlite3.connect(symptoms_db)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS symptoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT NOT NULL,
        symptom TEXT NOT NULL,
        severity INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.commit()
    print("Symptom database created successfully")
    conn.close()
except Exception as e:
    print(f"Error with symptom database: {str(e)}")

# Test chat history
try:
    print("\nTesting chat history file...")
    history_file = os.path.join(data_dir, "chat_history_test.json")
    test_data = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    with open(history_file, "w") as f:
        json.dump(test_data, f)
    print(f"Chat history file created at {history_file}")
except Exception as e:
    print(f"Error with chat history: {str(e)}")

print("\nAll tests completed. If there were no errors, the database setup should work correctly.") 