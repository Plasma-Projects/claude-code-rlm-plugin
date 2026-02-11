"""
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
