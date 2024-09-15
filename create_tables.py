from Youtube_project2.mysql_connector import create_connection
from Youtube_project2.queries import *


def create_database(connection, cursor, database):
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    databases = [db[0] for db in databases]
    if 'youtube' not in databases:
        create_database_query = f"CREATE DATABASE {database}"
        cursor.execute(create_database_query)
        print(f"Database {database} is created successfully!")
    else:
        print(f"Database {database} already exists!")


def create_tables(connection, cursor, database):
    cursor.execute(f"USE {database}")
    for query in create_table_queries:
        cursor.execute(query)
        connection.commit()


def drop_tables(connection, cursor, database):
    cursor.execute(f"USE {database}")
    for query in drop_table_queries:
        cursor.execute(query)
        connection.commit()


if __name__ == "__main__":
    connection = create_connection()
    cursor = connection.cursor()
    create_database(connection, cursor, database='youtube')
    drop_tables(connection, cursor, "youtube")
    create_tables(connection, cursor, database="youtube")
    connection.close()
