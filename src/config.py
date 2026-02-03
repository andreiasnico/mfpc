"""
Configuration and utilities for the distributed transaction system
"""

from typing import Dict, Any
import json
import os
from datetime import datetime
from loguru import logger
import sys

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure loguru logger
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    "logs/transaction_system.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
)

class SystemConfig:
    """System configuration settings"""
    
    # Transaction settings
    MAX_TRANSACTION_RETRIES = 3
    TRANSACTION_TIMEOUT_SECONDS = 30
    DEADLOCK_DETECTION_INTERVAL = 1.0
    
    # Concurrency control settings
    TIMESTAMP_PRECISION = 0.001
    MAX_CONCURRENT_TRANSACTIONS = 100
    MULTIVERSION_CLEANUP_THRESHOLD = 1000
    
    # Database settings
    DEFAULT_DATABASES = ['financial', 'inventory']
    TABLE_SCHEMAS = {
        'financial': {
            'users': ['id', 'username', 'email', 'password_hash', 'created_at', 'is_active'],
            'accounts': ['id', 'user_id', 'account_number', 'balance', 'account_type', 'created_at', 'is_active'],
            'transactions': ['id', 'from_account_id', 'to_account_id', 'amount', 'transaction_type', 'description', 'timestamp', 'status']
        },
        'inventory': {
            'categories': ['id', 'name', 'description', 'parent_id'],
            'products': ['id', 'name', 'description', 'price', 'stock_quantity', 'category_id', 'created_at', 'is_active'],
            'orders': ['id', 'user_id', 'total_amount', 'status', 'created_at', 'updated_at'],
            'order_items': ['id', 'order_id', 'product_id', 'quantity', 'unit_price', 'total_price']
        }
    }
    
    # CLI settings
    CLI_PROMPT_PREFIX = "DTS> "
    OUTPUT_FORMAT = "table"  # table, json, csv
    
    @classmethod
    def save_to_file(cls, filename: str):
        """Save configuration to file"""
        config_data = {
            'max_transaction_retries': cls.MAX_TRANSACTION_RETRIES,
            'transaction_timeout_seconds': cls.TRANSACTION_TIMEOUT_SECONDS,
            'deadlock_detection_interval': cls.DEADLOCK_DETECTION_INTERVAL,
            'timestamp_precision': cls.TIMESTAMP_PRECISION,
            'max_concurrent_transactions': cls.MAX_CONCURRENT_TRANSACTIONS,
            'multiversion_cleanup_threshold': cls.MULTIVERSION_CLEANUP_THRESHOLD,
            'default_databases': cls.DEFAULT_DATABASES,
            'table_schemas': cls.TABLE_SCHEMAS,
            'cli_prompt_prefix': cls.CLI_PROMPT_PREFIX,
            'output_format': cls.OUTPUT_FORMAT
        }
        
        with open(filename, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        logger.info(f"Configuration saved to {filename}")
    
    @classmethod
    def load_from_file(cls, filename: str):
        """Load configuration from file"""
        if not os.path.exists(filename):
            logger.warning(f"Configuration file {filename} not found, using defaults")
            return
        
        with open(filename, 'r') as f:
            config_data = json.load(f)
        
        cls.MAX_TRANSACTION_RETRIES = config_data.get('max_transaction_retries', cls.MAX_TRANSACTION_RETRIES)
        cls.TRANSACTION_TIMEOUT_SECONDS = config_data.get('transaction_timeout_seconds', cls.TRANSACTION_TIMEOUT_SECONDS)
        cls.DEADLOCK_DETECTION_INTERVAL = config_data.get('deadlock_detection_interval', cls.DEADLOCK_DETECTION_INTERVAL)
        cls.TIMESTAMP_PRECISION = config_data.get('timestamp_precision', cls.TIMESTAMP_PRECISION)
        cls.MAX_CONCURRENT_TRANSACTIONS = config_data.get('max_concurrent_transactions', cls.MAX_CONCURRENT_TRANSACTIONS)
        cls.MULTIVERSION_CLEANUP_THRESHOLD = config_data.get('multiversion_cleanup_threshold', cls.MULTIVERSION_CLEANUP_THRESHOLD)
        cls.DEFAULT_DATABASES = config_data.get('default_databases', cls.DEFAULT_DATABASES)
        cls.TABLE_SCHEMAS = config_data.get('table_schemas', cls.TABLE_SCHEMAS)
        cls.CLI_PROMPT_PREFIX = config_data.get('cli_prompt_prefix', cls.CLI_PROMPT_PREFIX)
        cls.OUTPUT_FORMAT = config_data.get('output_format', cls.OUTPUT_FORMAT)
        
        logger.info(f"Configuration loaded from {filename}")

class PerformanceMonitor:
    """Performance monitoring utility"""
    
    def __init__(self):
        self.metrics = {
            'transaction_count': 0,
            'operation_count': 0,
            'rollback_count': 0,
            'restart_count': 0,
            'deadlock_count': 0,
            'avg_transaction_duration': 0.0,
            'successful_transactions': 0,
            'failed_transactions': 0
        }
        self.transaction_times = []
        logger.debug("Performance monitor initialized")
    
    def record_transaction_start(self, transaction_id: str):
        """Record transaction start"""
        self.metrics['transaction_count'] += 1
        logger.debug(f"Transaction {transaction_id} started - total count: {self.metrics['transaction_count']}")
    
    def record_transaction_end(self, transaction_id: str, duration: float, success: bool):
        """Record transaction completion"""
        self.transaction_times.append(duration)
        
        if success:
            self.metrics['successful_transactions'] += 1
            logger.debug(f"Transaction {transaction_id} completed successfully in {duration:.3f}s")
        else:
            self.metrics['failed_transactions'] += 1
            logger.warning(f"Transaction {transaction_id} failed after {duration:.3f}s")
        
        # Update average duration
        self.metrics['avg_transaction_duration'] = sum(self.transaction_times) / len(self.transaction_times)
    
    def record_operation(self):
        """Record a database operation"""
        self.metrics['operation_count'] += 1
    
    def record_rollback(self):
        """Record a transaction rollback"""
        self.metrics['rollback_count'] += 1
        logger.info(f"Rollback recorded - total count: {self.metrics['rollback_count']}")
    
    def record_restart(self):
        """Record a transaction restart"""
        self.metrics['restart_count'] += 1
        logger.info(f"Transaction restart recorded - total count: {self.metrics['restart_count']}")
    
    def record_deadlock(self):
        """Record a deadlock detection"""
        self.metrics['deadlock_count'] += 1
        logger.warning(f"Deadlock detected - total count: {self.metrics['deadlock_count']}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def reset_metrics(self):
        """Reset all metrics"""
        logger.info("Resetting performance metrics")
        self.metrics = {
            'transaction_count': 0,
            'operation_count': 0,
            'rollback_count': 0,
            'restart_count': 0,
            'deadlock_count': 0,
            'avg_transaction_duration': 0.0,
            'successful_transactions': 0,
            'failed_transactions': 0
        }
        self.transaction_times = []

# Global instances
performance_monitor = PerformanceMonitor()