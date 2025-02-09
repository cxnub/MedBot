'''
Database helper class to interact with the MySQL database.
'''
import mysql.connector as mysql
from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector import Error

from src.utils.queries import *

class DBHelper:
    """
    A helper class to manage MySQL database connections and operations.
    Methods
    -------
    __init__(host, user, password, database)
        Initialize the database connection.
    create_connection()
        Create a database connection to the MySQL database.
    execute_query(query, params=None)
        Execute a single query.
    fetch_all(query, params=None)
        Fetch all results from a query.
    close_connection()
        Close the database connection.
    """
    def __init__(self, host, user, password, database):
        """Initialize the database connection."""
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        
        print(f"Connecting to database {database} at {host}...")
        
        # self.create_tables()
        
    def create_tables(self):
        """Create tables in the database."""
        try:
            # First connection to create database
            conn = mysql.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"======== Database {self.database} created successfully ========")
            
            for query in CREATE_TABLES_QUERIES:
                self.execute_query(query)
                
            print("======== Tables created successfully ========")
                
            for query in INSERT_DATA_QUERIES:
                self.execute_query(query)
                
            print("======== Data inserted successfully ========")
                
                    
        except Error as e:
            print(f"Error: {e}")
            return False

    def create_connection(self):
        """Create a database connection to the MySQL database."""
        try:
            conn = mysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
                
            return conn
        
        except Error as e:
            print(f"Error: {e}")

    def execute_query(self, query, params=None):
        """Execute a single query."""
        try:
            conn = self.create_connection()
            cursor = conn.cursor(buffered=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            
            results = cursor.fetchall()
            
            # convert results to a list of dictionaries
            results_dict = []
            if cursor.description:  # Only process if there are results
                for result in results:
                    result_dict = {}
                    for i, column in enumerate(cursor.description):
                        result_dict[column[0]] = result[i]
                    results_dict.append(result_dict)
            
            cursor.close()
            conn.close()
            
            return results_dict
            
        except Error as e:
            print(f"Error: {e}")
            return []

    def check_telegram_id(self, telegram_id):
        """Check if a user with the given telegram_id exists."""
        query = "SELECT * FROM users WHERE id = %s"
        params = (telegram_id,)
        return self.execute_query(query, params)

    def create_user(self, username, telegram_id):
        """Create a new user."""
        query = "INSERT INTO users (id, username, fun_mode) VALUES (%s, %s, %s)"
        params = (telegram_id, username, False)
        self.execute_query(query, params)

    def get_user(self, telegram_id):
        """Get a user by telegram_id."""
        query = "SELECT * FROM users WHERE id = %s"
        params = (telegram_id,)
        return self.execute_query(query, params)

    def create_appointment(self, user_id, doctor_id, hospital_id, datetime):
        """Create a new appointment."""
        query = "INSERT INTO appointments (user_id, doctor_id, hospital_id, datetime) VALUES (%s, %s, %s, %s)"
        params = (user_id, doctor_id, hospital_id, datetime)
        self.execute_query(query, params)

    def fetch_all_upcoming_appointments(self, user_id):
        """Fetch all appointments for a user."""
        query = "SELECT * FROM appointments WHERE user_id = %s AND datetime > now() ORDER BY datetime ASC"
        params = (int(user_id),)
        return self.execute_query(query, params)
    
    def get_appointment(self, user_id, appointment_id):
        """Get an appointment by appointment_id."""
        query = GET_APPOINTMENTS_QUERY
        params = (user_id, appointment_id)
        return self.execute_query(query, params)
    
    def cancel_appointment(self, user_id, appointment_id):
        """Cancel an appointment."""
        query = "DELETE FROM appointments WHERE user_id = %s AND id = %s"
        params = (user_id, appointment_id)
        self.execute_query(query, params)
    
    def get_hospitals(self):
        """Get all hospitals."""
        query = "SELECT * FROM hospitals"
        return self.execute_query(query)
    
    def get_doctors(self, hospital_id):
        """Get all doctors at a hospital."""
        query = "SELECT * FROM doctors WHERE hospital_id = %s"
        params = (hospital_id,)
        return self.execute_query(query, params)
    
    def get_available_slots(self, doctor_id, date: str):
        """Get available slots for a doctor at a hospital."""
        query = CHECK_AVAILABLE_SLOTS_QUERY
        params = (doctor_id, date)
        return self.execute_query(query, params)

    def change_fun_mode(self, telegram_id, fun_mode: bool):
        """Change the fun mode of a user."""
        query = "UPDATE users SET fun_mode = %s WHERE id = %s"
        params = (fun_mode, telegram_id)
        self.execute_query(query, params)

    def close_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed")