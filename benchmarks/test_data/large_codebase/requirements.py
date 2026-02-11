"""
Requirements and dependency management
"""

PRODUCTION_REQUIREMENTS = [
    'fastapi>=0.68.0',
    'uvicorn>=0.15.0',
    'sqlalchemy>=1.4.0',
    'psycopg2-binary>=2.9.0',
    'redis>=3.5.0',
    'celery>=5.2.0',
    'pydantic>=1.8.0',
    'python-jose[cryptography]>=3.3.0',
    'passlib[bcrypt]>=1.7.0',
    'python-multipart>=0.0.5',
    'email-validator>=1.1.0',
    'requests>=2.25.0',
    'httpx>=0.24.0',
    'aiofiles>=0.7.0',
    'python-decouple>=3.4',
]

DEVELOPMENT_REQUIREMENTS = [
    'pytest>=6.2.0',
    'pytest-asyncio>=0.15.0',
    'pytest-cov>=2.12.0',
    'black>=21.0.0',
    'isort>=5.9.0',
    'flake8>=3.9.0',
    'mypy>=0.910',
    'pre-commit>=2.15.0',
]

OPTIONAL_REQUIREMENTS = {
    'monitoring': [
        'prometheus-client>=0.11.0',
        'sentry-sdk>=1.3.0',
    ],
    'docs': [
        'sphinx>=4.0.0',
        'sphinx-rtd-theme>=0.5.0',
    ],
    'aws': [
        'boto3>=1.18.0',
        'botocore>=1.21.0',
    ]
}

def get_requirements(include_optional=False):
    """Get all requirements"""
    reqs = PRODUCTION_REQUIREMENTS + DEVELOPMENT_REQUIREMENTS
    
    if include_optional:
        for optional_reqs in OPTIONAL_REQUIREMENTS.values():
            reqs.extend(optional_reqs)
    
    return reqs

def check_dependencies():
    """Check if all dependencies are installed"""
    import pkg_resources
    
    requirements = get_requirements()
    missing = []
    
    for requirement in requirements:
        try:
            pkg_resources.require(requirement)
        except pkg_resources.DistributionNotFound:
            missing.append(requirement)
    
    return missing
