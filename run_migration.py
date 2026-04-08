from app.database import engine
from sqlalchemy import text

def migrate():
    print("Running database migration: Adding 'category' column to 'case_documents'...")
    try:
        with engine.connect() as conn:
            # Check if column exists first to be safe (MySQL style)
            # Adding try/except around the ALTER block is also effective
            try:
                conn.execute(text("ALTER TABLE case_documents ADD COLUMN category VARCHAR(50) DEFAULT NULL;"))
                conn.commit()
                print("Migration successful: 'category' column added.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("Note: 'category' column already exists.")
                else:
                    print(f"Migration error (possibly column already exists): {e}")
    except Exception as e:
        print(f"Fatal migration error: {e}")

if __name__ == "__main__":
    migrate()
