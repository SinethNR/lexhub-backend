from app.database import engine

def migrate():
    if not engine:
        print("Database engine not initialized.")
        return
    print("Creating statute_sections table...")
    from app.models import Base
    Base.metadata.create_all(bind=engine)
    print("Done!")

if __name__ == "__main__":
    migrate()
