from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from threading import RLock
import copy
from datetime import datetime
from loguru import logger

class DatabaseException(Exception):
    """Base exception for database operations"""
    pass

class Table:
    """In-memory table implementation"""
    
    def __init__(self, name: str, primary_key: str = 'id'):
        self.name = name
        self.primary_key = primary_key
        self.data: Dict[Any, Dict[str, Any]] = {}
        self.next_id = 1
        self.lock = RLock()
        self.indexes: Dict[str, Dict[Any, List[Any]]] = {}
    
    def insert(self, record: Dict[str, Any]) -> Any:
        """Insert a record into the table"""
        with self.lock:
            if self.primary_key not in record:
                record[self.primary_key] = self.next_id
                self.next_id += 1
            
            pk_value = record[self.primary_key]
            if pk_value in self.data:
                raise DatabaseException(f"Primary key {pk_value} already exists in table {self.name}")
            
            self.data[pk_value] = copy.deepcopy(record)
            self._update_indexes(record)
            return pk_value
    
    def select(self, primary_key: Any) -> Optional[Dict[str, Any]]:
        """Select a record by primary key"""
        with self.lock:
            return copy.deepcopy(self.data.get(primary_key))
    
    def select_all(self, condition: Optional[callable] = None) -> List[Dict[str, Any]]:
        """Select all records, optionally filtered by condition"""
        with self.lock:
            records = list(self.data.values())
            if condition:
                records = [r for r in records if condition(r)]
            return copy.deepcopy(records)
    
    def update(self, primary_key: Any, updates: Dict[str, Any]) -> bool:
        """Update a record by primary key"""
        with self.lock:
            if primary_key not in self.data:
                return False
            
            old_record = self.data[primary_key]
            updated_record = {**old_record, **updates}
            updated_record[self.primary_key] = primary_key  # Ensure PK doesn't change
            
            self.data[primary_key] = updated_record
            self._update_indexes(updated_record)
            return True
    
    def delete(self, primary_key: Any) -> bool:
        """Delete a record by primary key"""
        with self.lock:
            if primary_key not in self.data:
                return False
            
            del self.data[primary_key]
            self._remove_from_indexes(primary_key)
            return True
    
    def _update_indexes(self, record: Dict[str, Any]):
        """Update indexes for the record"""
        for field, value in record.items():
            if field not in self.indexes:
                self.indexes[field] = {}
            if value not in self.indexes[field]:
                self.indexes[field][value] = []
            
            pk_value = record[self.primary_key]
            if pk_value not in self.indexes[field][value]:
                self.indexes[field][value].append(pk_value)
    
    def _remove_from_indexes(self, primary_key: Any):
        """Remove record from all indexes"""
        for field_indexes in self.indexes.values():
            for value_list in field_indexes.values():
                if primary_key in value_list:
                    value_list.remove(primary_key)

class InMemoryDatabase:
    """In-memory database implementation"""
    
    def __init__(self, name: str):
        self.name = name
        self.tables: Dict[str, Table] = {}
        self.lock = RLock()
        self.transaction_log: List[Dict[str, Any]] = []
    
    def create_table(self, table_name: str, primary_key: str = 'id') -> Table:
        """Create a new table"""
        with self.lock:
            if table_name in self.tables:
                raise DatabaseException(f"Table {table_name} already exists")
            
            table = Table(table_name, primary_key)
            self.tables[table_name] = table
            return table
    
    def get_table(self, table_name: str) -> Table:
        """Get a table by name"""
        with self.lock:
            if table_name not in self.tables:
                raise DatabaseException(f"Table {table_name} does not exist")
            return self.tables[table_name]
    
    def execute_sql(self, operation: str, table_name: str, **kwargs) -> Any:
        """Execute a SQL-like operation"""
        with self.lock:
            table = self.get_table(table_name)
            
            # Log operation for transaction management
            log_entry = {
                'timestamp': datetime.now(),
                'operation': operation,
                'table': table_name,
                'params': kwargs
            }
            self.transaction_log.append(log_entry)
            
            if operation.upper() == 'INSERT':
                return table.insert(kwargs.get('record', {}))
            elif operation.upper() == 'SELECT':
                if 'primary_key' in kwargs:
                    return table.select(kwargs['primary_key'])
                else:
                    return table.select_all(kwargs.get('condition'))
            elif operation.upper() == 'UPDATE':
                return table.update(kwargs['primary_key'], kwargs['updates'])
            elif operation.upper() == 'DELETE':
                return table.delete(kwargs['primary_key'])
            else:
                raise DatabaseException(f"Unsupported operation: {operation}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.lock:
            stats = {
                'name': self.name,
                'tables': {},
                'total_operations': len(self.transaction_log)
            }
            
            for table_name, table in self.tables.items():
                stats['tables'][table_name] = {
                    'record_count': len(table.data),
                    'next_id': table.next_id
                }
            
            return stats

class DatabaseManager:
    """Manager for multiple in-memory databases"""
    
    def __init__(self):
        self.databases: Dict[str, InMemoryDatabase] = {}
        self.lock = RLock()
    
    def create_database(self, db_name: str) -> InMemoryDatabase:
        """Create a new database"""
        with self.lock:
            if db_name in self.databases:
                raise DatabaseException(f"Database {db_name} already exists")
            
            db = InMemoryDatabase(db_name)
            self.databases[db_name] = db
            return db
    
    def get_database(self, db_name: str) -> InMemoryDatabase:
        """Get a database by name"""
        with self.lock:
            if db_name not in self.databases:
                raise DatabaseException(f"Database {db_name} does not exist")
            return self.databases[db_name]
    
    def initialize_system_databases(self):
        """Initialize the two system databases with required tables"""
        with self.lock:
            logger.info("Initializing system databases")
            
            # Database 1: Financial System
            financial_db = self.create_database('financial')
            financial_db.create_table('users')
            financial_db.create_table('accounts') 
            financial_db.create_table('transactions')
            logger.debug("Financial database initialized with tables: users, accounts, transactions")
            
            # Database 2: Inventory/Order System
            inventory_db = self.create_database('inventory')
            inventory_db.create_table('categories')
            inventory_db.create_table('products')
            inventory_db.create_table('orders')
            inventory_db.create_table('order_items')
            logger.debug("Inventory database initialized with tables: categories, products, orders, order_items")
            
            logger.success("System databases initialized successfully")