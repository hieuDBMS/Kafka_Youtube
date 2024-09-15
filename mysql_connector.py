import mysql.connector
import json
from mysql.connector import Error


# Function to create a MySQL connection
def create_connection():
    try:
        connection = mysql.connector.connect(
            host="192.168.1.6",  # Use 'localhost' if you're running MySQL locally with Docker, otherwise use container IP
            port=3306,  # MySQL port exposed by Docker
            user="debezium",  # MySQL user (from your Docker Compose file)
            password="dbz",  # MySQL user password
            database="demo"  # The database you want to connect to
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connection: '{e}'")
        return None


# Function to execute a simple query
def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        myresult = cursor.fetchall()

        for x in myresult:
            print(x)

        connection.commit()
        print("Query executed successfully")
    except Error as e:
        print(f"Error query: '{e}'")


# Main logic
if __name__ == "__main__":
    # Create connection to the database
    connection = create_connection()

    if connection:
        # Example: Create a table in the demo database
        create_table_query = "SELECT * FROM ORDERS \G"
        execute_query(connection, create_table_query)

        # Close the connection
        connection.close()
