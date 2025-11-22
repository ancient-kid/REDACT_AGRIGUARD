"""
Database models and setup for AgriGuard using SQLAlchemy + SQLite
"""
import sqlalchemy
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from pathlib import Path

# Database file path
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_DIR / 'agriguard.db'}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class User(Base):
    """User table - stores basic user info from Clerk"""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, index=True)  # Clerk user ID
    email = Column(String, unique=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Upload(Base):
    """Upload history table"""
    __tablename__ = "uploads"
    
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, index=True)  # Foreign key to User
    file_name = Column(String)
    image_path = Column(String, nullable=True)  # Stored image path
    prediction_class = Column(String)
    severity = Column(String)
    confidence_healthy = Column(Float)
    confidence_diseased = Column(Float)
    summary = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Chat(Base):
    """Chat sessions table"""
    __tablename__ = "chats"
    
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, index=True)  # Foreign key to User
    session_id = Column(String, unique=True, index=True)  # Backend chat session ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    """Chat messages table"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String, index=True)  # Foreign key to Chat
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Dependency to get DB session
def get_db():
    """Dependency for FastAPI endpoints to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Initialize database
def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    
    # Migration: Add image_path column if it doesn't exist
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(sqlalchemy.text("PRAGMA table_info(uploads)"))
            columns = [row[1] for row in result]
            
            if 'image_path' not in columns:
                print("📝 Migrating database: Adding image_path column...")
                conn.execute(sqlalchemy.text("ALTER TABLE uploads ADD COLUMN image_path TEXT"))
                conn.commit()
                print("✅ Migration complete: image_path column added")
    except Exception as e:
        print(f"⚠️  Migration warning: {e}")
    
    print(f"✅ Database initialized at: {DATABASE_URL}")
