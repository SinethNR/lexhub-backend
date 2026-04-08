from sqlalchemy import text
from app.database import engine

def run_migrations():
    print("Running database migrations for Blogs...")
    with engine.connect() as conn:
        try:
            print("Adding 'image_url' to blogs table...")
            conn.execute(text("ALTER TABLE blogs ADD COLUMN image_url LONGTEXT NULL;"))
            conn.commit()
            print("Success!")
        except Exception as e:
            print(f"Skipped or failed image_url: {e}")

if __name__ == "__main__":
    run_migrations()
