"""Configuration module for the Mailer Microservice"""

import os
from dotenv import load_dotenv

ENV = os.getenv("ENV", "prod")

if ENV == "dev":
    load_dotenv(".env")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB", "trackify_mail")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# AWS SES Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")
SES_CHARSET = os.getenv("SES_CHARSET", "UTF-8")

# Microservices URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:80")
PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL", "http://pdf-service:80")
ENTRIES_SERVICE_URL = os.getenv("ENTRIES_SERVICE_URL", "http://entries-service:80")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8002"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_CREDENTIALS = os.getenv("CORS_CREDENTIALS", "True").lower() == "true"
CORS_METHODS = os.getenv("CORS_METHODS", "*").split(",")
CORS_HEADERS = os.getenv("CORS_HEADERS", "*").split(",")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
