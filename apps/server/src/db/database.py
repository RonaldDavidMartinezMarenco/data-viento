import mysql.connector
from mysql.connector import Error
from src.config import config
import logging

# Setup logging to track database operations
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Class to manage MySQL database connection
    Handles connection creation, closing, and error handling
    """
    
    def __init__(self):
        """
        Initialize the database connection object
        Stores connection details from config but doesn't connect yet
        """
        self.host = config.DB_HOST
        self.user = config.DB_USER
        self.password = config.DB_PASSWORD
        self.database = config.DB_NAME
        self.port = config.DB_PORT
        self.connection = None
    
    def connect(self):
        """
        Establishes connection to MySQL database
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection to MySQL
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                autocommit=False  # Require manual commit for transactions
            )
            
            # Check if connection is active
            if self.connection.is_connected():
                db_info = self.connection.get_server_info()
                logger.info(f"Successfully connected to MySQL Server version {db_info}")
                logger.info(f"Connected to database: {self.database}")
                return True
        
        except Error as err:
            # Catch any MySQL errors and log them
            if err.errno == 2003:
                logger.error("Cannot connect to MySQL Server on localhost")
            elif err.errno == 1045:
                logger.error("Access denied (check username/password)")
            elif err.errno == 1049:
                logger.error(f"Unknown database '{self.database}'")
            else:
                logger.error(f"Database connection error: {err}")
            
            return False
    
    def disconnect(self):
        """
        Closes the connection to MySQL database
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info("MySQL connection closed")
                return True
        except Error as err:
            logger.error(f"Error closing connection: {err}")
            return False
    
    def execute_query(self, query, params=None):
        """
        Execute a SELECT query and fetch results
        
        Args:
            query (str): SQL SELECT query
            params (tuple): Query parameters for parameterized queries (prevents SQL injection)
        
        Returns:
            list: List of tuples containing query results, or empty list if error
        """
        try:
            cursor = self.connection.cursor()
            
            # Execute query with parameters (safer than string concatenation)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch all results
            result = cursor.fetchall()
            cursor.close()
            
            logger.debug(f"Query executed successfully: {query}")
            return result
        
        except Error as err:
            logger.error(f"Error executing query: {err}")
            return []
    
    def execute_insert(self, query, params=None):
        """
        Execute an INSERT query and commit changes
        
        Args:
            query (str): SQL INSERT query
            params (tuple): Query parameters
        
        Returns:
            int: Last inserted row ID, or -1 if error
        """
        try:
            cursor = self.connection.cursor()
            
            # Execute insert with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Commit the transaction (saves changes to database)
            self.connection.commit()
            
            # Get the ID of the inserted row
            last_id = cursor.lastrowid
            cursor.close()
            
            logger.info(f"Data inserted successfully. Last inserted ID: {last_id}")
            return last_id
        
        except Error as err:
            # Rollback if error occurs (undo changes)
            self.connection.rollback()
            logger.error(f"Error inserting data: {err}")
            return -1
    
    def execute_bulk_insert(self, query, data_list):
        """
        Execute multiple INSERT operations at once (bulk insert)
        More efficient than inserting one row at a time
        
        Args:
            query (str): SQL INSERT query with placeholders
            data_list (list): List of tuples containing row data
        
        Returns:
            int: Number of rows inserted, or -1 if error
        """
        try:
            cursor = self.connection.cursor()
            
            # executemany executes the same query multiple times with different parameters
            cursor.executemany(query, data_list)
            
            # Commit all inserts
            self.connection.commit()
            
            rows_inserted = cursor.rowcount
            cursor.close()
            
            logger.info(f"Bulk insert successful. {rows_inserted} rows inserted")
            return rows_inserted
        
        except Error as err:
            # Rollback if error occurs
            self.connection.rollback()
            logger.error(f"Error in bulk insert: {err}")
            return -1
    
    def execute_update(self, query, params=None):
        """
        Execute an UPDATE query and commit changes
        
        Args:
            query (str): SQL UPDATE query
            params (tuple): Query parameters
        
        Returns:
            int: Number of rows affected, or -1 if error
        """
        try:
            cursor = self.connection.cursor()
            
            # Execute update with parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Commit the transaction
            self.connection.commit()
            
            rows_affected = cursor.rowcount
            cursor.close()
            
            logger.info(f"Update successful. {rows_affected} rows affected")
            return rows_affected
        
        except Error as err:
            # Rollback if error occurs
            self.connection.rollback()
            logger.error(f"Error updating data: {err}")
            return -1
    
    def is_connected(self):
        """
        Check if connection is active
        
        Returns:
            bool: True if connected, False otherwise
        """
        if self.connection and self.connection.is_connected():
            return True
        return False


# Create a global database instance to use throughout the app
db = DatabaseConnection()