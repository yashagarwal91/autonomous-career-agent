"""
Seed Data — Realistic AI/ML Job Postings
Run this once to populate the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal, JobPosting, init_db


SAMPLE_JOBS = [
    # senior
    {
        "title": "Senior AI Engineer",
        "company": "Flipkart",
        "location": "Bangalore",
        "experience_level": "Senior",
        "required_skills": "Python,LangChain,LangGraph,LLMs,RAG,FastAPI,Docker,Vector Databases,Prompt Engineering",
        "nice_to_have_skills": "LangSmith,CrewAI,AWS,Redis,Kubernetes",
        "salary_min": 25.0,
        "salary_max": 40.0,
        "job_type": "Full-time"
    },
    {
        "title": "Lead ML Engineer",
        "company": "Meesho",
        "location": "Bangalore",
        "experience_level": "Senior",
        "required_skills": "Python,PyTorch,MLflow,Kubernetes,FastAPI,SQL,Feature Engineering,Model Deployment",
        "nice_to_have_skills": "LLMs,Airflow,Spark,AWS SageMaker",
        "salary_min": 30.0,
        "salary_max": 45.0,
        "job_type": "Full-time"
    },
    {
        "title": "AI Research Engineer",
        "company": "Google DeepMind India",
        "location": "Bangalore",
        "experience_level": "Senior",
        "required_skills": "Python,PyTorch,Transformers,Research,LLMs,RLHF,Fine-tuning,NLP",
        "nice_to_have_skills": "JAX,TPU,Distributed Training,Published Papers",
        "salary_min": 40.0,
        "salary_max": 70.0,
        "job_type": "Full-time"
    },
    {
        "title": "Senior LLM Engineer",
        "company": "Sarvam AI",
        "location": "Bangalore",
        "experience_level": "Senior",
        "required_skills": "Python,LLMs,Fine-tuning,LangChain,RAG,Vector Databases,FastAPI,Prompt Engineering",
        "nice_to_have_skills": "LangGraph,RLHF,vLLM,Quantization",
        "salary_min": 28.0,
        "salary_max": 45.0,
        "job_type": "Full-time"
    },

    # mid
    {
        "title": "ML Engineer",
        "company": "Swiggy",
        "location": "Bangalore",
        "experience_level": "Mid",
        "required_skills": "Python,Scikit-learn,TensorFlow,SQL,MLflow,Docker,REST APIs,Data Pipelines",
        "nice_to_have_skills": "Spark,Airflow,Kubernetes,Feature Stores",
        "salary_min": 18.0,
        "salary_max": 28.0,
        "job_type": "Full-time"
    },
    {
        "title": "NLP Engineer",
        "company": "PhonePe",
        "location": "Bangalore",
        "experience_level": "Mid",
        "required_skills": "Python,NLP,Transformers,BERT,FastAPI,SQL,Text Classification,Named Entity Recognition",
        "nice_to_have_skills": "LLMs,LangChain,Vector Databases,RAG",
        "salary_min": 20.0,
        "salary_max": 32.0,
        "job_type": "Full-time"
    },
    {
        "title": "AI Engineer",
        "company": "Freshworks",
        "location": "Chennai",
        "experience_level": "Mid",
        "required_skills": "Python,LangChain,OpenAI APIs,FastAPI,PostgreSQL,Docker,REST APIs,Prompt Engineering",
        "nice_to_have_skills": "LangGraph,Vector Databases,Redis,LangSmith",
        "salary_min": 16.0,
        "salary_max": 25.0,
        "job_type": "Full-time"
    },
    {
        "title": "Data Scientist",
        "company": "Razorpay",
        "location": "Bangalore",
        "experience_level": "Mid",
        "required_skills": "Python,Machine Learning,SQL,Statistics,Scikit-learn,Pandas,Data Visualization,A/B Testing",
        "nice_to_have_skills": "Spark,Airflow,Deep Learning,MLflow",
        "salary_min": 18.0,
        "salary_max": 30.0,
        "job_type": "Full-time"
    },
    {
        "title": "Generative AI Engineer",
        "company": "Infosys",
        "location": "Pune",
        "experience_level": "Mid",
        "required_skills": "Python,LangChain,RAG,Vector Databases,OpenAI APIs,FastAPI,Prompt Engineering,SQL",
        "nice_to_have_skills": "LangGraph,LangSmith,Azure OpenAI,Docker",
        "salary_min": 14.0,
        "salary_max": 22.0,
        "job_type": "Full-time"
    },
    {
        "title": "MLOps Engineer",
        "company": "Ola",
        "location": "Bangalore",
        "experience_level": "Mid",
        "required_skills": "Python,MLflow,Docker,Kubernetes,CI/CD,SQL,Model Monitoring,FastAPI",
        "nice_to_have_skills": "Airflow,Spark,AWS,Terraform",
        "salary_min": 20.0,
        "salary_max": 32.0,
        "job_type": "Full-time"
    },

    # junior
    {
        "title": "Junior ML Engineer",
        "company": "Juspay",
        "location": "Bangalore",
        "experience_level": "Junior",
        "required_skills": "Python,Machine Learning,Scikit-learn,SQL,Pandas,Git,REST APIs",
        "nice_to_have_skills": "Deep Learning,Docker,FastAPI,NLP",
        "salary_min": 8.0,
        "salary_max": 14.0,
        "job_type": "Full-time"
    },
    {
        "title": "AI/ML Intern → Full Time",
        "company": "Postman",
        "location": "Bangalore",
        "experience_level": "Junior",
        "required_skills": "Python,Machine Learning,NLP,SQL,Git,Problem Solving",
        "nice_to_have_skills": "LangChain,LLMs,FastAPI,Docker",
        "salary_min": 6.0,
        "salary_max": 12.0,
        "job_type": "Full-time"
    },
]


def seed():
    init_db()
    db = SessionLocal()

    existing = db.query(JobPosting).count()
    if existing > 0:
        print(f"already seeded ({existing} jobs), skipping.")
        db.close()
        return

    for job in SAMPLE_JOBS:
        db.add(JobPosting(**job))

    db.commit()
    db.close()
    print(f"✅ seeded {len(SAMPLE_JOBS)} jobs")


if __name__ == "__main__":
    seed()