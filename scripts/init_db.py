import asyncio
import asyncpg
import os
import sys

# Ensure the root directory is in sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

async def init_db():
    print("Reading SQL file...")
    sql_path = os.path.join(os.path.dirname(__file__), "..", "app", "db", "sql", "001_init_app_chat.sql")
    
    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    print("Executing SQL against the database...")
    try:
        # Convert SQLAlchemy URL format (postgresql+asyncpg://) to standard asyncpg URL (postgresql://)
        db_url = str(settings.database_url).replace("postgresql+asyncpg://", "postgresql://")
        
        conn = await asyncpg.connect(db_url)
        await conn.execute(sql_content)
        await conn.close()
            
        print("Database successfully initialized via Python script!")
    except Exception as e:
        print(f"An error occurred during initialization: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
