from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from core.database.models import User

def test_db_connection():
    """Test database connection and User model."""
    engine = create_engine('postgresql://postgres:postgres@db:5432/cernoid')
    
    # Test raw SQL first
    with Session(engine) as session:
        # Check if we can connect and query
        result = session.execute(text('SELECT * FROM users LIMIT 1'))
        row = result.fetchone()
        print("Raw SQL result:", row)
        
        if row:
            # Try the ORM model
            user = session.query(User).first()
            print("ORM result:", user.username if user else None)
        else:
            print("No users found in database")

if __name__ == "__main__":
    test_db_connection() 