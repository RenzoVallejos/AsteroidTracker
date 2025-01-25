from flask import Flask, jsonify, render_template_string
import requests
import sqlite3
import json
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
import numpy as np

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
        # Clear old data from the database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM raw_data')  # Clear all rows in the raw_data table
        conn.commit()
        conn.close()

        # Fetch new data from the NASA API
        api_url = "https://api.nasa.gov/neo/rest/v1/feed?start_date=2025-01-01&end_date=2025-01-08&api_key=DEMO_KEY"
        response = requests.get(api_url)

        if response.status_code == 200:
            data = response.json()
            save_to_db(data)  # Save raw data to the database
            return jsonify({"status": "Data saved to the database"})
        else:
            return jsonify({"error": "Failed to fetch data", "status_code": response.status_code})
    except Exception as e:
        return jsonify({"error": str(e)})


# Function to transform data from the database
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
        # Check if near_earth_objects is a dictionary
        if isinstance(item.get('near_earth_objects', {}), dict):
            for date, asteroids in item['near_earth_objects'].items():
                for asteroid in asteroids:
                    approach_data = asteroid.get('close_approach_data', [{}])[0]
                    neo_data.append({
                        'id': asteroid.get('id', 'unknown'),
                        'name': asteroid.get('name', 'unknown'),
                        'close_approach_date': approach_data.get('close_approach_date', None),
                        'miss_distance_km': approach_data.get('miss_distance', {}).get('kilometers', None),
                        'velocity_kph': approach_data.get('relative_velocity', {}).get('kilometers_per_hour', None)
                    })
        else:
            print("Warning: near_earth_objects is not a dictionary:", item.get('near_earth_objects', None))

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(neo_data)

    # Ensure numeric columns are properly cast
    df['miss_distance_km'] = pd.to_numeric(df['miss_distance_km'], errors='coerce')
    df['velocity_kph'] = pd.to_numeric(df['velocity_kph'], errors='coerce')

    conn.close()
    return df


# Route to display transformed data as an HTML table
@app.route('/transform', methods=['GET'])
def display_transformed_data():
    df = transform_data()
    return df.to_html()  # Display the DataFrame as an HTML table

# Route to export transformed data to a CSV file
@app.route('/export', methods=['GET'])
def export_data():
    df = transform_data()
    csv_path = 'transformed_data.csv'
    df.to_csv(csv_path, index=False)
    return jsonify({"status": "Data exported to CSV", "path": csv_path})

# Route to analyze data (closest and fastest NEO)
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

# Route to visualize data with Plotly
@app.route('/visualize', methods=['GET'])
def visualize_data():
    try:
        df = transform_data()

        # Drop rows with NaN values in critical columns
        df = df.dropna(subset=['miss_distance_km', 'velocity_kph'])

        # Create a scatter plot with enhanced features
        fig = px.scatter(
            df,
            x='close_approach_date',
            y='miss_distance_km',
            size='velocity_kph',
            color='velocity_kph',  # Use velocity as the color scale
            color_continuous_scale='Viridis',  # Gradient color scale
            hover_name='name',
            title='NEO Close Approaches Visualization',
            labels={
                'close_approach_date': 'Close Approach Date',
                'miss_distance_km': 'Miss Distance (km)',
                'velocity_kph': 'Velocity (km/h)'
            }
        )
        fig.update_traces(marker=dict(opacity=0.7))  # Increase bubble transparency

        # Simplify the X-axis ticks to remove redundancy
        fig.update_layout(
            xaxis=dict(
                tickmode='array',  # Show unique dates only
                tickvals=df['close_approach_date'].unique(),  # Use only unique dates
                tickformat="%Y-%m-%d",  # Format as "YYYY-MM-DD"
                title="Close Approach Date"
            )
        )

        # Highlight closest and fastest NEOs with annotations
        closest_neo = df.loc[df['miss_distance_km'].idxmin()]
        fastest_neo = df.loc[df['velocity_kph'].idxmax()]

        fig.add_annotation(
            x=closest_neo['close_approach_date'],
            y=closest_neo['miss_distance_km'],
            text="Closest NEO",
            showarrow=True,
            arrowhead=2,
            ax=-40,
            ay=-40
        )
        fig.add_annotation(
            x=fastest_neo['close_approach_date'],
            y=fastest_neo['miss_distance_km'],
            text="Fastest NEO",
            showarrow=True,
            arrowhead=2,
            ax=40,
            ay=-40
        )

        # Render the chart as an HTML page
        return render_template_string(fig.to_html(full_html=False, include_plotlyjs='cdn'))
    except Exception as e:
        return jsonify({"error": str(e)})

# Route to perform clustering based on velocity
@app.route('/cluster', methods=['GET'])
def cluster_neos():
    try:
        df = transform_data()

        # Drop NaN values and prepare velocity data for clustering
        df = df.dropna(subset=['velocity_kph'])
        velocities = df[['velocity_kph']].values

        # Perform KMeans clustering
        kmeans = KMeans(n_clusters=3, random_state=42)  # Create 3 clusters
        df['cluster'] = kmeans.fit_predict(velocities)

        # Convert cluster centers and results to a response
        clusters = kmeans.cluster_centers_.flatten().tolist()
        cluster_counts = df['cluster'].value_counts().to_dict()

        return jsonify({
            "clusters": clusters,
            "cluster_counts": cluster_counts,
            "data": df[['name', 'velocity_kph', 'cluster']].to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# Route to perform linear regression for future close approach prediction
@app.route('/predict', methods=['GET'])
def predict_close_approach():
    try:
        df = transform_data()

        # Convert close_approach_date to numeric for regression
        df['close_approach_date_numeric'] = pd.to_datetime(df['close_approach_date']).map(pd.Timestamp.timestamp)
        df = df.dropna(subset=['miss_distance_km', 'close_approach_date_numeric'])

        # Prepare data for linear regression
        X = df[['close_approach_date_numeric']].values
        y = df['miss_distance_km'].values.astype(float)

        # Train a linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Predict the miss distance for a future date (e.g., 1 week from the last date)
        future_date = df['close_approach_date_numeric'].max() + 7 * 24 * 3600  # Add 7 days
        future_distance = model.predict([[future_date]])

        return jsonify({
            "future_date": pd.to_datetime(future_date, unit='s').strftime('%Y-%m-%d'),
            "predicted_miss_distance_km": future_distance[0]
        })
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
