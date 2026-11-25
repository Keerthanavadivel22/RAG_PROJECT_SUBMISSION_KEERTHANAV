import mysql.connector


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Keera@123",
        database="ragdb",
        
    )


# Test connection
try:
    conn = get_connection()
    print("Connected to MySQL successfully!")

    

except mysql.connector.Error as err:
    print(" Error:", err)

finally:
    if 'conn' in locals() and conn.is_connected():
       
        conn.close()
        print("Connection closed.")