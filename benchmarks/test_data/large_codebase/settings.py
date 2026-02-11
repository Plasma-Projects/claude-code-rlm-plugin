"""
Application settings and configuration
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Database settings
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'name': os.getenv('DB_NAME', 'myapp'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'pool_size': 10,
    'max_overflow': 20,
    'echo': ENVIRONMENT == 'development'
}

# Redis settings
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD'),
    'socket_timeout': 5,
    'socket_connect_timeout': 5
}

# API settings
API_CONFIG = {
    'host': os.getenv('API_HOST', '0.0.0.0'),
    'port': int(os.getenv('API_PORT', 8000)),
    'debug': ENVIRONMENT == 'development',
    'cors_origins': ['http://localhost:3000', 'https://myapp.com'],
    'rate_limit': {
        'requests': 100,
        'window': 60
    }
}

# Authentication settings
AUTH_CONFIG = {
    'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key'),
    'algorithm': 'HS256',
    'access_token_expire_minutes': 30,
    'refresh_token_expire_days': 7,
    'password_min_length': 8
}

# Logging settings
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# Task queue settings
CELERY_CONFIG = {
    'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379'),
    'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True
}

# Email settings
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER'),
    'smtp_port': int(os.getenv('SMTP_PORT', 587)),
    'username': os.getenv('SMTP_USERNAME'),
    'password': os.getenv('SMTP_PASSWORD'),
    'use_tls': True
}

# Feature flags
FEATURE_FLAGS = {
    'enable_new_ui': True,
    'enable_analytics': True,
    'enable_caching': True,
    'enable_monitoring': True
}
