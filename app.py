from flask import Flask, jsonify
import requests
import sqlite3
import json
import pandas as pd

app = Flask(__name__)

# Function to save raw data into the database
def save_to_db(data):
    conn = sqlite3.connect('data.db')  # Creates or opens a SQLite database
    cursor = conn.cursor()

    # Create a table for storing raw data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS raw_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        json_data TEXT
    )
    ''')

    # Insert the raw JSON data
    cursor.execute('INSERT INTO raw_data (json_data) VALUES (?)', (json.dumps(data),))
    conn.commit()
    conn.close()

# Route to fetch raw data and store it in the database
@app.route('/fetch-and-store', methods=['GET'])
def fetch_and_store():
    try:
        api_url = "https://api.nasa.gov/neo/rest/v1/feed?start_date=2015-09-07&end_date=2015-09-08&api_key=DEMO_KEY"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            save_to_db(data)  # Save raw data to the database
            return jsonify({"status": "Data saved to the database"})
        else:
            return jsonify({"error": "Failed to fetch data", "status_code": response.status_code})
    except Exception as e:
        return jsonify({"error": str(e)})

def transform_data():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Fetch raw JSON data from the database
    cursor.execute('SELECT json_data FROM raw_data')
    rows = cursor.fetchall()
    raw_json = [json.loads(row[0]) for row in rows]

    # Extract and flatten the JSON into a DataFrame
    neo_data = []
    for item in raw_json:
        for date, asteroids in item['near_earth_objects'].items():
            for asteroid in asteroids:
                neo_data.append({
                    'id': asteroid['id'],
                    'name': asteroid['name'],
                    'close_approach_date': date,
                    'miss_distance_km': asteroid['close_approach_data'][0]['miss_distance']['kilometers'],
                    'velocity_kph': asteroid['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']
                })

    df = pd.DataFrame(neo_data)
    conn.close()
    return df

@app.route('/transform', methods=['GET'])
def display_transformed_data():
    df = transform_data()
    return df.to_html()  # Display the DataFrame as an HTML table

@app.route('/export', methods=['GET'])
def export_data():
    df = transform_data()
    csv_path = 'transformed_data.csv'
    df.to_csv(csv_path, index=False)
    return jsonify({"status": "Data exported to CSV", "path": csv_path})

@app.route('/analyze', methods=['GET'])
def analyze_data():
    df = transform_data()

    # Find the closest and fastest NEO
    closest_neo = df.loc[df['miss_distance_km'].astype(float).idxmin()]
    fastest_neo = df.loc[df['velocity_kph'].astype(float).idxmax()]

    result = {
        "closest_neo": closest_neo.to_dict(),
        "fastest_neo": fastest_neo.to_dict()
    }

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
