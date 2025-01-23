import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('data.db')  # Ensure 'data.db' is in the same directory or provide the correct path
cursor = conn.cursor()

# Execute a query to fetch all data from the table
cursor.execute('SELECT * FROM raw_data')

# Print the fetched data
print(cursor.fetchall())

# Close the connection
conn.close()
