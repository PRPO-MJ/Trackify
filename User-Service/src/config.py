"""Configuration module for the User Management Microservice"""

import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "prod")

if ENV == "dev":
    load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", None)  
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "80"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "True").lower() == "true"
CORS_METHODS = os.getenv("CORS_METHODS", "*").split(",")
CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(",")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"