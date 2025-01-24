# 🚀 NEO Data Pipeline: Project Instructions

This guide will help you set up and run the Near-Earth Object (NEO) Data Pipeline in your environment.

---

# 🛠️ Prerequisites

1. **Install Python**: Ensure you have Python 3.x installed.
    - [Download Python](https://www.python.org/downloads/)
2. **Install Dependencies**:
    - Flask
    - Requests
    - Pandas
# 📁 Project Structure
bash
Copy
Edit
project-root/
├── app.py              # Main Flask application
├── data.db             # SQLite database (auto-created)
├── transformed_data.csv # CSV export (auto-created after export)
└── README.md           # Project documentation
# 🚀 Running the Application
1. Clone the repository:
- git clone <repository_url>
- cd <repository_directory>
2. Run the Flask server:
- python app.py
3. Access the endpoints:
- Open your browser and visit: http://127.0.0.1:5000/


## 🔗 Endpoints Overview

1. **Fetch and Store Data**
    - **URL**: `/fetch-and-store`
    - **Method**: GET
    - **Description**: Fetches NEO data from NASA's API and stores it in a SQLite database.
    - **Response**:
      ```json
      {
        "status": "Data saved to the database"
      }
      ```

2. **Transform Data**
    - **URL**: `/transform`
    - **Method**: GET
    - **Description**: Transforms stored raw data into a structured HTML table.

3. **Export Data**
    - **URL**: `/export`
    - **Method**: GET
    - **Description**: Exports the transformed data to a CSV file.
    - **Response**:
      ```json
      {
        "status": "Data exported to CSV",
        "path": "transformed_data.csv"
      }
      ```

4. **Analyze Data**
    - **URL**: `/analyze`
    - **Method**: GET
    - **Description**: Finds and returns the closest and fastest NEOs.
    - **Response**:
      ```json
      {
        "closest_neo": {
          "id": "1",
          "name": "Sample NEO",
          "close_approach_date": "YYYY-MM-DD",
          "miss_distance_km": "123456.789",
          "velocity_kph": "65432.1"
        },
        "fastest_neo": {
          "id": "2",
          "name": "Another NEO",
          "close_approach_date": "YYYY-MM-DD",
          "miss_distance_km": "987654.321",
          "velocity_kph": "123456.7"
        }
      }
      ```

# 📝 Notes
Replace DEMO_KEY in the NASA API URL with your personal NASA API Key.
The SQLite database file (data.db) is created automatically.
The CSV export file (transformed_data.csv) will appear in the project directory after the /export endpoint is accessed.