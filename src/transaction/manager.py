from typing import Dict, List, Any, Optional, Callable
import time
import copy
from datetime import datetime
from loguru import logger

from .concurrency import (
    ConcurrencyController, Transaction, TransactionStatus, 
    TransactionException, DeadlockException, Operation
)
from database.inmemory_db import DatabaseManager, DatabaseException

class TransactionManager:
    """Main transaction manager implementing ACID properties"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.database_manager = database_manager
        self.concurrency_controller = ConcurrencyController()
        self.active_transactions: Dict[str, str] = {}  # thread_id -> transaction_id
        self.transaction_log: List[Dict[str, Any]] = []
        self.rollback_log: Dict[str, List[Dict[str, Any]]] = {}  # transaction_id -> rollback operations
        self.max_retries = 3
    
    def begin_transaction(self, thread_id: str = None) -> str:
        """Begin a new transaction"""
        if thread_id is None:
            thread_id = str(time.time())
        
        transaction_id = self.concurrency_controller.begin_transaction()
        self.active_transactions[thread_id] = transaction_id
        self.rollback_log[transaction_id] = []
        
        self.log_operation("BEGIN_TRANSACTION", transaction_id, {
            'thread_id': thread_id,
            'timestamp': datetime.now()
        })
        
        return transaction_id
    
    def execute_operation(self, thread_id: str, operation_type: str, 
                         database_name: str, table_name: str, 
                         record_id: Any = None, data: Dict[str, Any] = None) -> Any:
        """Execute a database operation within a transaction"""
        
        if thread_id not in self.active_transactions:
            raise TransactionException("No active transaction for this thread")
        
        transaction_id = self.active_transactions[thread_id]
        transaction = self.concurrency_controller.transactions[transaction_id]
        
        if transaction.status != TransactionStatus.ACTIVE:
            raise TransactionException("Transaction is not active")
        
        resource_id = f"{database_name}.{table_name}.{record_id}" if record_id else f"{database_name}.{table_name}"
        
        # Validate operation based on timestamp ordering
        if operation_type.upper() in ['SELECT']:
            if not self.concurrency_controller.validate_read(transaction_id, resource_id):
                # Restart transaction
                self._restart_transaction(transaction_id, thread_id)
                raise TransactionException("Transaction restarted due to read validation failure")
        
        elif operation_type.upper() in ['INSERT', 'UPDATE', 'DELETE']:
            if not self.concurrency_controller.validate_write(transaction_id, resource_id):
                # Restart transaction
                self._restart_transaction(transaction_id, thread_id)
                raise TransactionException("Transaction restarted due to write validation failure")
        
        # Check for deadlock before proceeding
        deadlocked_transaction = self.concurrency_controller.detect_deadlock()
        if deadlocked_transaction == transaction_id:
            self._restart_transaction(transaction_id, thread_id)
            raise DeadlockException("Transaction restarted due to deadlock")
        
        # Execute the actual database operation
        try:
            result = self._execute_database_operation(
                transaction_id, operation_type, database_name, 
                table_name, record_id, data
            )
            
            # Update transaction metadata
            if operation_type.upper() == 'SELECT':
                transaction.read_set.add((database_name, table_name, record_id))
            else:
                transaction.write_set.add((database_name, table_name, record_id))
            
            # Create operation record
            operation = Operation(
                operation_id=f"{transaction_id}_{len(transaction.operations)}",
                operation_type=operation_type.upper(),
                database_name=database_name,
                table_name=table_name,
                record_id=record_id,
                data=data or {}
            )
            
            transaction.operations.append(operation)
            
            return result
            
        except Exception as e:
            # Log the error and prepare for rollback
            self.log_operation("OPERATION_ERROR", transaction_id, {
                'error': str(e),
                'operation': operation_type,
                'resource': resource_id
            })
            raise TransactionException(f"Operation failed: {str(e)}")
    
    def commit_transaction(self, thread_id: str) -> bool:
        """Commit a transaction"""
        if thread_id not in self.active_transactions:
            raise TransactionException("No active transaction for this thread")
        
        transaction_id = self.active_transactions[thread_id]
        transaction = self.concurrency_controller.transactions[transaction_id]
        
        try:
            # Set status to preparing
            transaction.status = TransactionStatus.PREPARING
            
            # Final validation before commit
            for db, table, record_id in transaction.read_set:
                resource_id = f"{db}.{table}.{record_id}"
                if not self.concurrency_controller.validate_read(transaction_id, resource_id):
                    raise TransactionException("Read validation failed during commit")
            
            for db, table, record_id in transaction.write_set:
                resource_id = f"{db}.{table}.{record_id}"
                if not self.concurrency_controller.validate_write(transaction_id, resource_id):
                    raise TransactionException("Write validation failed during commit")
            
            # Commit all multiversion data
            for db, table, record_id in transaction.write_set:
                resource_id = f"{db}.{table}.{record_id}"
                self.concurrency_controller.multiversion_storage.commit_version(resource_id, transaction_id)
            
            # Update transaction status
            transaction.status = TransactionStatus.COMMITTED
            transaction.commit_timestamp = time.time()
            
            # Clean up
            self.concurrency_controller.remove_wait_edges(transaction_id)
            del self.active_transactions[thread_id]
            del self.rollback_log[transaction_id]
            
            self.log_operation("COMMIT_TRANSACTION", transaction_id, {
                'timestamp': datetime.now(),
                'operations_count': len(transaction.operations)
            })
            
            return True
            
        except Exception as e:
            # Commit failed, rollback
            self.rollback_transaction(thread_id)
            raise TransactionException(f"Commit failed: {str(e)}")
    
    def rollback_transaction(self, thread_id: str) -> bool:
        """Rollback a transaction"""
        if thread_id not in self.active_transactions:
            return False
        
        transaction_id = self.active_transactions[thread_id]
        transaction = self.concurrency_controller.transactions[transaction_id]
        
        try:
            # Execute rollback operations in reverse order
            rollback_operations = self.rollback_log.get(transaction_id, [])
            
            for rollback_op in reversed(rollback_operations):
                self._execute_rollback_operation(rollback_op)
            
            # Abort all multiversion data
            for db, table, record_id in transaction.write_set:
                resource_id = f"{db}.{table}.{record_id}"
                self.concurrency_controller.multiversion_storage.abort_version(resource_id, transaction_id)
            
            # Update transaction status
            transaction.status = TransactionStatus.ABORTED
            
            # Clean up
            self.concurrency_controller.remove_wait_edges(transaction_id)
            del self.active_transactions[thread_id]
            del self.rollback_log[transaction_id]
            
            self.log_operation("ROLLBACK_TRANSACTION", transaction_id, {
                'timestamp': datetime.now(),
                'rollback_operations_count': len(rollback_operations)
            })
            
            return True
            
        except Exception as e:
            self.log_operation("ROLLBACK_ERROR", transaction_id, {
                'error': str(e)
            })
            return False
    
    def _execute_database_operation(self, transaction_id: str, operation_type: str,
                                  database_name: str, table_name: str,
                                  record_id: Any, data: Dict[str, Any]) -> Any:
        """Execute the actual database operation"""
        
        database = self.database_manager.get_database(database_name)
        operation_type = operation_type.upper()
        
        # Store rollback information before executing
        if operation_type in ['INSERT', 'UPDATE', 'DELETE']:
            self._prepare_rollback_info(transaction_id, operation_type, 
                                      database_name, table_name, record_id)
        
        if operation_type == 'SELECT':
            if record_id is not None:
                return database.execute_sql('SELECT', table_name, primary_key=record_id)
            else:
                condition = data.get('condition') if data else None
                return database.execute_sql('SELECT', table_name, condition=condition)
        
        elif operation_type == 'INSERT':
            return database.execute_sql('INSERT', table_name, record=data)
        
        elif operation_type == 'UPDATE':
            return database.execute_sql('UPDATE', table_name, 
                                      primary_key=record_id, updates=data)
        
        elif operation_type == 'DELETE':
            return database.execute_sql('DELETE', table_name, primary_key=record_id)
        
        else:
            raise TransactionException(f"Unsupported operation: {operation_type}")
    
    def _prepare_rollback_info(self, transaction_id: str, operation_type: str,
                              database_name: str, table_name: str, record_id: Any):
        """Prepare rollback information for an operation"""
        
        rollback_info = {
            'operation_type': operation_type,
            'database_name': database_name,
            'table_name': table_name,
            'record_id': record_id,
            'timestamp': datetime.now()
        }
        
        # For UPDATE and DELETE, store the original data
        if operation_type in ['UPDATE', 'DELETE']:
            try:
                database = self.database_manager.get_database(database_name)
                original_data = database.execute_sql('SELECT', table_name, primary_key=record_id)
                rollback_info['original_data'] = original_data
            except:
                rollback_info['original_data'] = None
        
        self.rollback_log[transaction_id].append(rollback_info)
    
    def _execute_rollback_operation(self, rollback_info: Dict[str, Any]):
        """Execute a single rollback operation"""
        
        operation_type = rollback_info['operation_type']
        database_name = rollback_info['database_name']
        table_name = rollback_info['table_name']
        record_id = rollback_info['record_id']
        original_data = rollback_info.get('original_data')
        
        database = self.database_manager.get_database(database_name)
        
        if operation_type == 'INSERT':
            # Rollback INSERT by deleting the record
            database.execute_sql('DELETE', table_name, primary_key=record_id)
        
        elif operation_type == 'UPDATE':
            # Rollback UPDATE by restoring original data
            if original_data:
                database.execute_sql('UPDATE', table_name, 
                                   primary_key=record_id, updates=original_data)
        
        elif operation_type == 'DELETE':
            # Rollback DELETE by reinserting the original data
            if original_data:
                database.execute_sql('INSERT', table_name, record=original_data)
    
    def _restart_transaction(self, old_transaction_id: str, thread_id: str):
        """Restart a transaction (for timestamp-based concurrency control)"""
        
        # Rollback current transaction
        self.rollback_transaction(thread_id)
        
        # Start a new transaction
        new_transaction_id = self.begin_transaction(thread_id)
        
        self.log_operation("RESTART_TRANSACTION", old_transaction_id, {
            'new_transaction_id': new_transaction_id,
            'timestamp': datetime.now()
        })
    
    def log_operation(self, operation_type: str, transaction_id: str, details: Dict[str, Any]):
        """Log transaction operations for debugging and auditing"""
        log_entry = {
            'timestamp': datetime.now(),
            'operation_type': operation_type,
            'transaction_id': transaction_id,
            'details': details
        }
        self.transaction_log.append(log_entry)
        
        # Log with appropriate level based on operation type
        if operation_type in ['ROLLBACK_TRANSACTION', 'OPERATION_ERROR', 'ROLLBACK_ERROR']:
            logger.warning(f"{operation_type} - TX:{transaction_id[:8]} - {details}")
        elif operation_type in ['RESTART_TRANSACTION']:
            logger.info(f"Transaction restarted - TX:{transaction_id[:8]} - {details}")
        else:
            logger.debug(f"{operation_type} - TX:{transaction_id[:8]} - {details}")
    
    def get_transaction_statistics(self) -> Dict[str, Any]:
        """Get transaction system statistics"""
        active_count = len(self.active_transactions)
        total_transactions = len(self.concurrency_controller.transactions)
        
        return {
            'active_transactions': active_count,
            'total_transactions': total_transactions,
            'log_entries': len(self.transaction_log),
            'multiversion_resources': len(self.concurrency_controller.multiversion_storage.versions)
        }