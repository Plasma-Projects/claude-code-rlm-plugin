#!/usr/bin/env python3
"""
Generate large test datasets for RLM plugin benchmarking
"""

import json
import csv
import random
import string
from datetime import datetime, timedelta
import os
from pathlib import Path

# Configuration
DATA_DIR = Path(__file__).parent / "test_data"
DATA_DIR.mkdir(exist_ok=True)

def generate_large_json(size_mb=1.5):
    """Generate large JSON file (1MB+)"""
    print(f"Generating large JSON file (~{size_mb}MB)...")
    
    # Calculate approximate number of records needed
    records_needed = int((size_mb * 1024 * 1024) // 200)  # ~200 bytes per record
    
    data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_records": records_needed,
            "version": "1.0"
        },
        "users": [],
        "transactions": [],
        "products": []
    }
    
    # Generate users
    for i in range(records_needed // 3):
        user = {
            "id": i,
            "username": f"user_{i}",
            "email": f"user_{i}@example.com",
            "profile": {
                "first_name": random.choice(["John", "Jane", "Bob", "Alice", "Charlie", "Diana"]),
                "last_name": random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]),
                "age": random.randint(18, 80),
                "address": {
                    "street": f"{random.randint(1, 9999)} {''.join(random.choices(string.ascii_lowercase, k=8)).title()} St",
                    "city": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                    "state": random.choice(["NY", "CA", "IL", "TX", "AZ"]),
                    "zip": f"{random.randint(10000, 99999)}"
                }
            },
            "preferences": {
                "notifications": random.choice([True, False]),
                "theme": random.choice(["light", "dark", "auto"]),
                "language": random.choice(["en", "es", "fr", "de"])
            },
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat()
        }
        data["users"].append(user)
    
    # Generate transactions
    for i in range(records_needed // 3):
        transaction = {
            "id": f"txn_{i}",
            "user_id": random.randint(0, len(data["users"]) - 1),
            "amount": round(random.uniform(10.0, 1000.0), 2),
            "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
            "type": random.choice(["purchase", "refund", "subscription", "fee"]),
            "status": random.choice(["completed", "pending", "failed", "cancelled"]),
            "timestamp": (datetime.now() - timedelta(hours=random.randint(1, 8760))).isoformat(),
            "metadata": {
                "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
                "merchant_id": f"merch_{random.randint(1, 1000)}",
                "category": random.choice(["retail", "dining", "travel", "entertainment", "utilities"])
            }
        }
        data["transactions"].append(transaction)
    
    # Generate products
    for i in range(records_needed // 3):
        product = {
            "id": f"prod_{i}",
            "name": f"{''.join(random.choices(string.ascii_lowercase, k=8)).title()} Product",
            "description": f"High-quality {''.join(random.choices(string.ascii_lowercase, k=20))} for everyday use",
            "price": round(random.uniform(5.0, 500.0), 2),
            "category": random.choice(["electronics", "clothing", "home", "sports", "books"]),
            "tags": random.sample(["new", "sale", "popular", "limited", "premium", "eco"], k=random.randint(1, 3)),
            "inventory": {
                "stock": random.randint(0, 1000),
                "reserved": random.randint(0, 50),
                "warehouse": f"WH_{random.randint(1, 10)}"
            },
            "metrics": {
                "views": random.randint(0, 10000),
                "purchases": random.randint(0, 500),
                "rating": round(random.uniform(1.0, 5.0), 1),
                "reviews_count": random.randint(0, 200)
            }
        }
        data["products"].append(product)
    
    output_file = DATA_DIR / "large_dataset.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"✓ Generated {output_file} ({size:.2f}MB)")
    return output_file

def generate_large_csv(rows=15000):
    """Generate large CSV dataset (10,000+ rows)"""
    print(f"Generating CSV file with {rows:,} rows...")
    
    output_file = DATA_DIR / "large_dataset.csv"
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            'id', 'timestamp', 'user_id', 'event_type', 'value',
            'category', 'source', 'ip_address', 'user_agent', 
            'session_id', 'conversion', 'revenue', 'location'
        ])
        
        # Data rows
        for i in range(rows):
            timestamp = datetime.now() - timedelta(
                minutes=random.randint(0, 525600)  # Up to a year ago
            )
            
            row = [
                i,
                timestamp.isoformat(),
                f"user_{random.randint(1, 10000)}",
                random.choice(['page_view', 'click', 'purchase', 'signup', 'logout']),
                random.randint(1, 100),
                random.choice(['marketing', 'organic', 'referral', 'direct', 'social']),
                random.choice(['web', 'mobile', 'api', 'email']),
                f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
                ]),
                f"sess_{random.randint(100000, 999999)}",
                random.choice([True, False, None]),
                round(random.uniform(0, 1000), 2) if random.random() > 0.7 else None,
                random.choice(['US', 'CA', 'UK', 'DE', 'FR', 'JP', 'AU'])
            ]
            writer.writerow(row)
    
    size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"✓ Generated {output_file} ({size:.2f}MB, {rows:,} rows)")
    return output_file

def generate_log_file(size_mb=5):
    """Generate large log file with timestamps"""
    print(f"Generating log file (~{size_mb}MB)...")
    
    output_file = DATA_DIR / "application.log"
    
    log_levels = ['INFO', 'WARN', 'ERROR', 'DEBUG']
    components = ['auth', 'db', 'api', 'cache', 'queue', 'worker']
    messages = [
        'Request processed successfully',
        'Connection timeout occurred',
        'User authentication failed',
        'Database query executed',
        'Cache miss for key',
        'Task queued for processing',
        'Invalid parameter received',
        'Memory usage threshold exceeded',
        'File uploaded successfully',
        'Service unavailable'
    ]
    
    target_size = size_mb * 1024 * 1024
    current_size = 0
    
    with open(output_file, 'w') as f:
        while current_size < target_size:
            timestamp = datetime.now() - timedelta(
                seconds=random.randint(0, 86400 * 30)  # Last 30 days
            )
            
            level = random.choice(log_levels)
            component = random.choice(components)
            message = random.choice(messages)
            
            # Add some structured data occasionally
            if random.random() > 0.8:
                extra = f" user_id={random.randint(1, 10000)} duration={random.randint(1, 5000)}ms"
            else:
                extra = ""
            
            log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} [{level:5}] {component}: {message}{extra}\n"
            
            f.write(log_line)
            current_size += len(log_line.encode('utf-8'))
    
    size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"✓ Generated {output_file} ({size:.2f}MB)")
    return output_file

def generate_large_codebase():
    """Generate large Python codebase simulation"""
    print("Generating large Python codebase...")
    
    code_dir = DATA_DIR / "large_codebase"
    code_dir.mkdir(exist_ok=True)
    
    # Generate multiple Python files
    files_created = []
    
    # Main application structure
    modules = [
        'models', 'views', 'controllers', 'services', 'utils', 
        'auth', 'database', 'api', 'tasks', 'config'
    ]
    
    for module in modules:
        module_dir = code_dir / module
        module_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = module_dir / "__init__.py"
        with open(init_file, 'w') as f:
            f.write(f'"""The {module} module"""\n')
        files_created.append(init_file)
        
        # Create multiple Python files in each module
        for i in range(5):
            py_file = module_dir / f"{module}_{i}.py"
            with open(py_file, 'w') as f:
                f.write(generate_python_code(module, i))
            files_created.append(py_file)
    
    # Generate some large individual files
    large_files = ['main.py', 'settings.py', 'requirements.py']
    for filename in large_files:
        large_file = code_dir / filename
        with open(large_file, 'w') as f:
            f.write(generate_large_python_file(filename))
        files_created.append(large_file)
    
    total_size = sum(os.path.getsize(f) for f in files_created) / (1024 * 1024)
    print(f"✓ Generated {len(files_created)} Python files ({total_size:.2f}MB total)")
    return code_dir

def generate_python_code(module, index):
    """Generate realistic Python code"""
    class_name = f"{module.title()}{''.join(random.choices(string.ascii_uppercase, k=3))}"
    
    code = f'''"""
{module} module implementation
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class {class_name}:
    """
    {class_name} class for handling {module} operations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {{}}
        self.initialized = False
        self._cache = {{}}
        
    def initialize(self) -> bool:
        """Initialize the {module} component"""
        try:
            self._setup_logging()
            self._load_configuration()
            self._validate_dependencies()
            self.initialized = True
            logger.info(f"{class_name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {class_name}: {{e}}")
            return False
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_configuration(self):
        """Load configuration from various sources"""
        config_sources = [
            'config.json',
            'settings.py',
            os.environ
        ]
        
        for source in config_sources:
            try:
                if isinstance(source, str) and source.endswith('.json'):
                    with open(source) as f:
                        config_data = json.load(f)
                        self.config.update(config_data)
                elif source == os.environ:
                    env_vars = {{k: v for k, v in source.items() if k.startswith('{module.upper()}_')}}
                    self.config.update(env_vars)
            except FileNotFoundError:
                logger.warning(f"Configuration source {{source}} not found")
            except Exception as e:
                logger.error(f"Error loading configuration from {{source}}: {{e}}")
    
    def _validate_dependencies(self):
        """Validate required dependencies"""
        required_deps = ['requests', 'sqlalchemy', 'redis']
        missing_deps = []
        
        for dep in required_deps:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            raise ImportError(f"Missing dependencies: {{missing_deps}}")
    
    def process_data(self, data: Union[Dict, List]) -> Dict:
        """Process input data"""
        if not self.initialized:
            raise RuntimeError("Component not initialized")
        
        start_time = datetime.now()
        
        try:
            if isinstance(data, dict):
                result = self._process_dict(data)
            elif isinstance(data, list):
                result = self._process_list(data)
            else:
                raise ValueError(f"Unsupported data type: {{type(data)}}")
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {{
                'success': True,
                'result': result,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }}
        
        except Exception as e:
            logger.error(f"Error processing data: {{e}}")
            return {{
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }}
    
    def _process_dict(self, data: Dict) -> Dict:
        """Process dictionary data"""
        processed = {{}}
        for key, value in data.items():
            if isinstance(value, str):
                processed[key] = value.upper()
            elif isinstance(value, (int, float)):
                processed[key] = value * 2
            elif isinstance(value, list):
                processed[key] = [item for item in value if item is not None]
            else:
                processed[key] = value
        return processed
    
    def _process_list(self, data: List) -> List:
        """Process list data"""
        return [item for item in data if self._is_valid_item(item)]
    
    def _is_valid_item(self, item) -> bool:
        """Validate individual items"""
        if item is None:
            return False
        if isinstance(item, str) and len(item.strip()) == 0:
            return False
        return True
    
    def get_stats(self) -> Dict:
        """Get component statistics"""
        return {{
            'initialized': self.initialized,
            'cache_size': len(self._cache),
            'config_keys': list(self.config.keys()),
            'module': '{module}',
            'index': {index}
        }}


# Module-level functions
def create_{module}_instance(config: Optional[Dict] = None) -> {class_name}:
    """Factory function to create {module} instance"""
    instance = {class_name}(config)
    instance.initialize()
    return instance


def validate_{module}_config(config: Dict) -> bool:
    """Validate {module} configuration"""
    required_keys = ['enabled', 'timeout', 'max_retries']
    return all(key in config for key in required_keys)


# Constants
DEFAULT_CONFIG = {{
    'enabled': True,
    'timeout': 30,
    'max_retries': 3,
    'batch_size': 100,
    'cache_ttl': 3600
}}

VERSION = "1.{index}.0"
AUTHOR = "Generated Code"
'''
    
    return code

def generate_large_python_file(filename):
    """Generate a large Python file"""
    if filename == 'main.py':
        return '''"""
Main application entry point
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Import all modules
from models import *
from views import *
from controllers import *
from services import *
from utils import *
from auth import *
from database import *
from api import *
from tasks import *
from config import *


class Application:
    """Main application class"""
    
    def __init__(self):
        self.config = {}
        self.services = {}
        self.running = False
        self.tasks = []
        
    async def initialize(self):
        """Initialize application"""
        print("Initializing application...")
        
        # Load configuration
        await self.load_configuration()
        
        # Initialize services
        await self.initialize_services()
        
        # Setup signal handlers
        self.setup_signal_handlers()
        
        print("Application initialized successfully")
    
    async def load_configuration(self):
        """Load application configuration"""
        config_files = [
            'config/production.json',
            'config/staging.json', 
            'config/development.json'
        ]
        
        for config_file in config_files:
            try:
                with open(config_file) as f:
                    config = json.load(f)
                    self.config.update(config)
            except FileNotFoundError:
                continue
    
    async def initialize_services(self):
        """Initialize all application services"""
        service_configs = self.config.get('services', {})
        
        for service_name, config in service_configs.items():
            try:
                service_class = globals().get(f"{service_name.title()}Service")
                if service_class:
                    service = service_class(config)
                    await service.initialize()
                    self.services[service_name] = service
            except Exception as e:
                logging.error(f"Failed to initialize {service_name}: {e}")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            print(f"Received signal {signum}, shutting down...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Main application loop"""
        self.running = True
        print("Starting application...")
        
        try:
            while self.running:
                await self.process_tasks()
                await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"Application error: {e}")
        finally:
            await self.shutdown()
    
    async def process_tasks(self):
        """Process background tasks"""
        for service in self.services.values():
            if hasattr(service, 'process'):
                await service.process()
    
    async def shutdown(self):
        """Shutdown application gracefully"""
        print("Shutting down application...")
        
        for service in self.services.values():
            if hasattr(service, 'shutdown'):
                await service.shutdown()
        
        print("Application shutdown complete")


async def main():
    """Main entry point"""
    app = Application()
    await app.initialize()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
'''
    
    elif filename == 'settings.py':
        return '''"""
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
'''
    
    else:  # requirements.py
        return '''"""
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
'''

def main():
    """Generate all test datasets"""
    print("Generating comprehensive test datasets for RLM plugin benchmarking...\n")
    
    # Generate all test files
    json_file = generate_large_json(1.5)
    csv_file = generate_large_csv(15000)
    log_file = generate_log_file(5)
    code_dir = generate_large_codebase()
    
    print(f"\n✅ All test data generated in: {DATA_DIR}")
    print("Files created:")
    print(f"  - {json_file.name} (large JSON dataset)")
    print(f"  - {csv_file.name} (large CSV dataset)")  
    print(f"  - {log_file.name} (large log file)")
    print(f"  - {code_dir.name}/ (large Python codebase)")

if __name__ == "__main__":
    main()