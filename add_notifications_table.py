from app.database import engine

def migrate():
    if not engine:
        print("Database engine not initialized.")
        return
    print(f"Connecting to database...")
    try:
        with engine.connect() as conn:
            print("Successfully connected to database.")
            print("Creating Notifications table...")
            from app.models import Base
            Base.metadata.create_all(bind=engine)
            print("Table created successfully.")
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
