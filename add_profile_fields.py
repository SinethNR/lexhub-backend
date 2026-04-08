from sqlalchemy import text
from app.database import engine

def run_migrations():
    print("Running database migrations for profiles...")
    with engine.connect() as conn:
        try:
            print("Adding 'occupation' to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN occupation VARCHAR(255) NULL;"))
            conn.commit()
        except Exception as e:
            print(f"Skipped occupation: {e}")

        try:
            print("Adding 'linkedin_url' to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN linkedin_url VARCHAR(500) NULL;"))
            conn.commit()
        except Exception as e:
            print(f"Skipped linkedin_url: {e}")

        try:
            print("Adding 'phone' to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(50) NULL;"))
            conn.commit()
        except Exception as e:
            print(f"Skipped phone: {e}")

        # The lawyer_publications table will be automatically created by main.py's Base.metadata.create_all()
        # but just to be sure we can trigger it here by importing the model and binding
        print("Importing models to ensure table creation...")
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        
    print("Done! Profile fields and lawyer_publications table are ready.")

if __name__ == "__main__":
    run_migrations()
