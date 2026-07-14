"""
Database setup for Autonomous Career Intelligence Agent
SQLite + SQLAlchemy — no server needed
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, String,
    Text, DateTime, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db/career_agent.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # required for sqlite with fastapi
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class JobPosting(Base):
    __tablename__ = "job_postings"

    id                  = Column(Integer, primary_key=True, index=True)
    title               = Column(String(100), nullable=False)
    company             = Column(String(100), nullable=False)
    location            = Column(String(100))
    experience_level    = Column(String(20))
    required_skills     = Column(Text)              # comma-separated
    nice_to_have_skills = Column(Text)
    salary_min          = Column(Float)             # in LPA
    salary_max          = Column(Float)
    job_type            = Column(String(20))
    created_at          = Column(DateTime, default=datetime.utcnow)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id            = Column(Integer, primary_key=True, index=True)
    session_id    = Column(String(100), unique=True, index=True)
    resume_skills = Column(Text)
    target_role   = Column(String(100))
    skill_gaps    = Column(Text)
    learning_plan = Column(Text)
    eval_score    = Column(Float)
    created_at    = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized")


if __name__ == "__main__":
    init_db()