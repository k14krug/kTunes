import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('kTunes.sqlite')
cur = conn.cursor()

# Get the list of all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()

for table in tables:
    table_name = table[0]
    print(f"\nTable: {table_name}\n{'-'*40}")

    # Print the schema of the table
    cur.execute(f"PRAGMA table_info({table_name});")
    schema = cur.fetchall()
    print("\nSchema:")
    for column in schema:
        print(f"\tColumn ID: {column[0]}, Column Name: {column[1]}, Data Type: {column[2]}")

    # Print the indexes of the table
    cur.execute(f"PRAGMA index_list({table_name});")
    indexes = cur.fetchall()
    print("\nIndexes:")
    for index in indexes:
        index_name = index[1]
        print(f"\tIndex Name: {index_name}")
        cur.execute(f"PRAGMA index_info({index_name});")
        index_info = cur.fetchall()
        for info in index_info:
            print(f"\t\tColumn Name: {info[2]}")

# Close the connection
conn.close()