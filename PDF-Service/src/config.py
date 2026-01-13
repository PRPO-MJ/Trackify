"""Configuration module for the PDF Microservice"""

import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "prod")

if ENV == "dev" or ENV == "prod":
    load_dotenv(".env")

# Database Configuration (optional, for caching/history)
DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "trackify_pdf")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# Microservices URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:80")
GOALS_SERVICE_URL = os.getenv("GOALS_SERVICE_URL", "http://goals-service:80")
ENTRIES_SERVICE_URL = os.getenv("ENTRIES_SERVICE_URL", "http://entries-service:80")

# PDF Configuration
PDF_TEMP_DIR = os.getenv("PDF_TEMP_DIR", "/tmp/trackify_pdfs")
PDF_STORAGE_PATH = os.getenv("PDF_STORAGE_PATH", "./pdfs")
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "10"))

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8005"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "True").lower() == "true"
CORS_METHODS = os.getenv("CORS_METHODS", "*").split(",")
CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(",")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
