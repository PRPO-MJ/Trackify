"""Configuration module for the Entries Service"""

import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "prod")

if ENV == "dev" or ENV == "prod":
    load_dotenv(".env")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "trackify_entries")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Microservices URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:80")
GOALS_SERVICE_URL = os.getenv("GOALS_SERVICE_URL", "http://goals-service:80")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8004"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "True").lower() == "true"
CORS_METHODS = os.getenv("CORS_METHODS", "*").split(",")
CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(",")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
