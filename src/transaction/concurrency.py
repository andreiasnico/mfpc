from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock, RLock
import time
import uuid
import copy

class TransactionStatus(Enum):
    ACTIVE = "active"
    COMMITTED = "committed"
    ABORTED = "aborted"
    PREPARING = "preparing"

class LockType(Enum):
    SHARED = "shared"
    EXCLUSIVE = "exclusive"

@dataclass
class TimestampInfo:
    """Timestamp information for multiversion concurrency control"""
    read_timestamp: float
    write_timestamp: float
    commit_timestamp: Optional[float] = None

@dataclass
class DataVersion:
    """Data version for multiversion storage"""
    value: Any
    timestamp: float
    transaction_id: str
    committed: bool = False

@dataclass
class Lock:
    """Lock information"""
    transaction_id: str
    lock_type: LockType
    resource_id: str
    acquired_at: float

@dataclass
class Operation:
    """Database operation in a transaction"""
    operation_id: str
    operation_type: str  # SELECT, INSERT, UPDATE, DELETE
    database_name: str
    table_name: str
    record_id: Any
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class Transaction:
    """Transaction object"""
    transaction_id: str
    start_timestamp: float
    status: TransactionStatus = TransactionStatus.ACTIVE
    operations: List[Operation] = field(default_factory=list)
    read_set: Set[Tuple[str, str, Any]] = field(default_factory=set)  # (db, table, record_id)
    write_set: Set[Tuple[str, str, Any]] = field(default_factory=set)
    locks_held: Set[str] = field(default_factory=set)  # resource_ids
    commit_timestamp: Optional[float] = None
    
class TransactionException(Exception):
    """Transaction-related exceptions"""
    pass

class DeadlockException(TransactionException):
    """Deadlock detected exception"""
    pass

class MultiversionStorage:
    """Multiversion storage for timestamps-based concurrency control"""
    
    def __init__(self):
        self.versions: Dict[str, List[DataVersion]] = {}  # resource_id -> versions
        self.lock = RLock()
    
    def read_value(self, resource_id: str, read_timestamp: float) -> Optional[Any]:
        """Read value for given timestamp (find appropriate version)"""
        with self.lock:
            if resource_id not in self.versions:
                return None
            
            # Find the latest committed version with timestamp <= read_timestamp
            valid_versions = [
                v for v in self.versions[resource_id] 
                if v.committed and v.timestamp <= read_timestamp
            ]
            
            if not valid_versions:
                return None
            
            # Return the latest valid version
            latest_version = max(valid_versions, key=lambda v: v.timestamp)
            return copy.deepcopy(latest_version.value)
    
    def write_value(self, resource_id: str, value: Any, write_timestamp: float, 
                   transaction_id: str) -> bool:
        """Write value with given timestamp"""
        with self.lock:
            if resource_id not in self.versions:
                self.versions[resource_id] = []
            
            # Create new version
            new_version = DataVersion(
                value=copy.deepcopy(value),
                timestamp=write_timestamp,
                transaction_id=transaction_id,
                committed=False
            )
            
            self.versions[resource_id].append(new_version)
            return True
    
    def commit_version(self, resource_id: str, transaction_id: str) -> bool:
        """Mark versions written by transaction as committed"""
        with self.lock:
            if resource_id not in self.versions:
                return False
            
            for version in self.versions[resource_id]:
                if version.transaction_id == transaction_id:
                    version.committed = True
            
            return True
    
    def abort_version(self, resource_id: str, transaction_id: str) -> bool:
        """Remove uncommitted versions written by transaction"""
        with self.lock:
            if resource_id not in self.versions:
                return False
            
            self.versions[resource_id] = [
                v for v in self.versions[resource_id] 
                if v.transaction_id != transaction_id
            ]
            
            return True

class ConcurrencyController:
    """Timestamp-based concurrency controller with multiversion support"""
    
    def __init__(self):
        self.transactions: Dict[str, Transaction] = {}
        self.multiversion_storage = MultiversionStorage()
        self.lock_table: Dict[str, List[Lock]] = {}  # resource_id -> locks
        self.timestamp_counter = 0
        self.lock = RLock()
        self.wait_for_graph: Dict[str, Set[str]] = {}  # transaction_id -> set of transactions waiting for
    
    def begin_transaction(self) -> str:
        """Begin a new transaction"""
        with self.lock:
            transaction_id = str(uuid.uuid4())
            start_timestamp = time.time() + self.timestamp_counter
            self.timestamp_counter += 0.001  # Ensure unique timestamps
            
            transaction = Transaction(
                transaction_id=transaction_id,
                start_timestamp=start_timestamp,
                status=TransactionStatus.ACTIVE
            )
            
            self.transactions[transaction_id] = transaction
            self.wait_for_graph[transaction_id] = set()
            return transaction_id
    
    def validate_read(self, transaction_id: str, resource_id: str) -> bool:
        """Validate read operation using timestamp ordering"""
        with self.lock:
            transaction = self.transactions[transaction_id]
            
            # Check if any younger transaction has written to this resource
            for other_txn in self.transactions.values():
                if (other_txn.transaction_id != transaction_id and 
                    other_txn.start_timestamp > transaction.start_timestamp):
                    # Check write set
                    for db, table, record_id in other_txn.write_set:
                        if f"{db}.{table}.{record_id}" == resource_id:
                            # Younger transaction wrote - must abort current transaction
                            return False
            
            return True
    
    def validate_write(self, transaction_id: str, resource_id: str) -> bool:
        """Validate write operation using timestamp ordering"""
        with self.lock:
            transaction = self.transactions[transaction_id]
            
            # Check if any younger transaction has read or written to this resource
            for other_txn in self.transactions.values():
                if (other_txn.transaction_id != transaction_id and 
                    other_txn.start_timestamp > transaction.start_timestamp):
                    
                    # Check read set
                    for db, table, record_id in other_txn.read_set:
                        if f"{db}.{table}.{record_id}" == resource_id:
                            return False
                    
                    # Check write set
                    for db, table, record_id in other_txn.write_set:
                        if f"{db}.{table}.{record_id}" == resource_id:
                            return False
            
            return True
    
    def detect_deadlock(self) -> Optional[str]:
        """Detect deadlock using wait-for graph"""
        with self.lock:
            # Implement cycle detection in wait-for graph
            visited = set()
            rec_stack = set()
            
            def has_cycle(transaction_id: str) -> bool:
                visited.add(transaction_id)
                rec_stack.add(transaction_id)
                
                for neighbor in self.wait_for_graph.get(transaction_id, set()):
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
                
                rec_stack.remove(transaction_id)
                return False
            
            for txn_id in self.transactions.keys():
                if txn_id not in visited:
                    if has_cycle(txn_id):
                        # Return the youngest transaction in the cycle (to abort)
                        cycle_transactions = [
                            txn_id for txn_id in self.transactions.keys()
                            if txn_id in rec_stack
                        ]
                        if cycle_transactions:
                            youngest = max(
                                cycle_transactions,
                                key=lambda t: self.transactions[t].start_timestamp
                            )
                            return youngest
            
            return None
    
    def add_wait_edge(self, waiter: str, holder: str):
        """Add edge to wait-for graph"""
        with self.lock:
            if waiter in self.wait_for_graph:
                self.wait_for_graph[waiter].add(holder)
    
    def remove_wait_edges(self, transaction_id: str):
        """Remove all edges involving a transaction"""
        with self.lock:
            # Remove outgoing edges
            if transaction_id in self.wait_for_graph:
                self.wait_for_graph[transaction_id].clear()
            
            # Remove incoming edges
            for txn_id in self.wait_for_graph:
                self.wait_for_graph[txn_id].discard(transaction_id)