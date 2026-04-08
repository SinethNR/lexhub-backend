from sqlalchemy import text
from app.database import engine

def migrate():
    if not engine:
        print("Database engine not initialized.")
        return
    print(f"Connecting to database...")
    try:
        # Ensure the connection works
        with engine.connect() as conn:
            print("Successfully connected to database.")
            
            # Use SQLAlchemy's metadata to create tables automatically
            # This will create 'cases', 'case_documents', and 'case_notes' 
            # if they don't already exist.
            print("Creating Case management tables...")
            from app.models import Base
            # This will detect the new models Case, CaseDocument, CaseNote 
            # because they were added to app.models.
            Base.metadata.create_all(bind=engine)
            
            print("Tables created successfully.")
            
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
