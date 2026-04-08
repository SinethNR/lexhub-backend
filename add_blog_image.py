from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# We expect .env to point to the Aiven instance:
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:root@localhost/lexhub")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

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
