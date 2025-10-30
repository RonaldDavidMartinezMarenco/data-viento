import sys
from pathlib import Path

# Add the parent directory to the path so we can import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.database import db
import logging

# Setup logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_database_connection():
    """
    Test if the database connection is working correctly
    This function will:
    1. Try to connect to the database
    2. Execute a test query
    3. Display connection details
    4. Disconnect
    """
    
    print("\n" + "="*60)
    print("DATABASE CONNECTION TEST")
    print("="*60 + "\n")
    
    # Step 1: Attempt connection
    print("Step 1: Attempting to connect to database...")
    print("-" * 60)
    
    connection_result = db.connect()
    
    if not connection_result:
        print("FAILED: Could not connect to database")
        print("\nPlease check:")
        print("  ✓ Is MySQL running?")
        print("  ✓ Are your .env credentials correct?")
        print("    - DB_HOST: should be 'localhost'")
        print("    - DB_USER: should be 'x'")
        print("    - DB_PASSWORD: should be 'y'")
        print("    - DB_NAME: should be 'data_viento_database'")
        print("  ✓ Does the database exist?")
        return False
    
    print("SUCCESS: Connected to database!")
    print(f"   Host: {db.host}")
    print(f"   User: {db.user}")
    print(f"   Database: {db.database}")
    print(f"   Port: {db.port}\n")
    
    # Step 2: Test a simple query
    print("Step 2: Testing a simple SELECT query...")
    print("-" * 60)
    
    try:
        # Execute a simple query to get database version
        result = db.execute_query("SELECT VERSION()")
        
        if result:
            mysql_version = result[0][0]
            print(f"Query successful!")
            print(f"   MySQL Version: {mysql_version}\n")
        else:
            print("Query returned no results\n")
            return False
    
    except Exception as e:
        print(f"Query failed: {e}\n")
        return False
    
    # Step 3: Check if tables exist
    print("Step 3: Checking if required tables exist...")
    print("-" * 60)
    
    # Query to get list of all tables in the database
    tables_query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = %s
    """
    
    try:
        tables = db.execute_query(tables_query, (db.database,))
        
        if tables:
            print(f"Found {len(tables)} tables in database:\n")
            for table in tables:
                print(f"   • {table[0]}")
            print()
        else:
            print("WARNING: No tables found in database")
            print("   This is normal if you haven't created the schema yet.\n")
    
    except Exception as e:
        print(f"Error checking tables: {e}\n")
        return False
    
    # Step 4: Test a specific table (if users table exists)
    print("Step 4: Testing specific table access...")
    print("-" * 60)
    
    try:
        # Try to count rows in users table
        result = db.execute_query("SELECT COUNT(*) FROM users")
        
        if result is not None:
            user_count = result[0][0]
            print(f"Successfully accessed 'users' table")
            print(f"   Total users: {user_count}\n")
        else:
            print("Could not access users table\n")
    
    except Exception as e:
        print(f"Warning: Could not query users table")
        print(f"   This might mean the table doesn't exist yet")
        print(f"   Error: {e}\n")
    
    # Step 5: Disconnect
    print("Step 5: Disconnecting from database...")
    print("-" * 60)
    
    disconnect_result = db.disconnect()
    
    if disconnect_result:
        print("Disconnected successfully\n")
    else:
        print("Failed to disconnect\n")
    
    # Final Summary
    print("="*60)
    print("DATABASE CONNECTION TEST COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    """
    Run the test when this file is executed
    """
    success = test_database_connection()
    sys.exit(0 if success else 1)