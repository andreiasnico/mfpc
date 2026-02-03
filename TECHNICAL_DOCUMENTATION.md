# Distributed Transaction System - Technical Documentation

## Project Overview

This project implements a sophisticated distributed transactional system that meets all the specified requirements for a concurrent distributed application. The system demonstrates advanced concepts in database transaction management, concurrency control, and distributed systems.

## Architecture

### Multi-Tier Architecture

```
┌─────────────────────────────────────┐
│           CLI Interface             │
│         (User Interface)            │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         Business Layer              │
│        (Middleware/Services)        │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│      Transaction Manager            │
│    (Concurrency & ACID Control)     │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Database Layer               │
│    (Two In-Memory Databases)       │
└─────────────────────────────────────┘
```

### Component Details

#### 1. Database Layer (`src/database/`)
- **Two separate in-memory databases**: 
  - `financial`: Users, Accounts, Transactions (3 tables)
  - `inventory`: Categories, Products, Orders, OrderItems (4 tables)
- **Features**:
  - Thread-safe operations with RLock
  - Primary key management
  - Index support
  - SQL-like operations (INSERT, SELECT, UPDATE, DELETE)

#### 2. Transaction Layer (`src/transaction/`)
- **Concurrency Controller** (`concurrency.py`):
  - Timestamp-based concurrency control
  - Multiversion storage for read consistency
  - Deadlock detection using wait-for graphs
  - Automatic transaction restart mechanism
  
- **Transaction Manager** (`manager.py`):
  - ACID property implementation
  - Distributed transaction coordination
  - Rollback mechanisms
  - Operation logging and auditing

#### 3. Business Layer (`src/business/`)
- **Service Classes**:
  - `UserService`: User management operations
  - `AccountService`: Banking account operations
  - `TransactionService`: Money transfers and payments
  - `ProductService`: Product inventory management
  - `OrderService`: Order processing with payment
  - `CategoryService`: Product categorization

#### 4. CLI Interface (`src/cli/`)
- Interactive command-line interface
- 8+ business operations
- Real-time transaction monitoring
- User-friendly error handling and feedback

## Key Features Implemented

### 1. ACID Properties

#### Atomicity
- All operations within a transaction are treated as a single unit
- If any operation fails, the entire transaction is rolled back
- Demonstrated in complex order processing (multiple table updates)

#### Consistency
- Database constraints are enforced
- Business rules are validated before operations
- Cross-database referential integrity maintained

#### Isolation
- Timestamp-based concurrency control
- Multiversion storage prevents dirty reads
- Phantom reads prevented through timestamp validation

#### Durability
- Transaction logs maintain operation history
- Rollback information stored for each operation
- State persistence across operation failures

### 2. Timestamp-Based Concurrency Control

#### Implementation Details
- Each transaction receives a unique timestamp at start
- Read/Write validation based on timestamp ordering
- Automatic restart for timestamp violations
- Multiversion storage for consistent reads

#### Algorithm
```python
# Read Validation
if younger_transaction_wrote_to_resource:
    restart_current_transaction()

# Write Validation  
if younger_transaction_read_or_wrote_resource:
    restart_current_transaction()
```

### 3. Multiversion Storage

#### Features
- Multiple versions of data maintained
- Timestamp-based version selection
- Automatic cleanup of old versions
- Consistent read views for long transactions

#### Version Management
- Each write creates new version
- Versions marked as committed/uncommitted
- Read operations find appropriate version
- Garbage collection of obsolete versions

### 4. Deadlock Detection and Resolution

#### Wait-For Graph Algorithm
- Maintains graph of transaction dependencies
- Cycle detection identifies deadlocks
- Youngest transaction in cycle is aborted
- Automatic restart of aborted transactions

#### Implementation
```python
def detect_deadlock() -> Optional[str]:
    # Build wait-for graph
    # Detect cycles using DFS
    # Return youngest transaction to abort
```

### 5. Rollback Mechanisms

#### Per-Operation Rollback
- Before each operation, rollback info is stored
- INSERT rollback: DELETE the record
- UPDATE rollback: Restore original values
- DELETE rollback: Re-INSERT original record

#### Transaction-Level Rollback
- Operations executed in reverse order
- Multiversion storage cleaned up
- Wait-for graph edges removed
- Transaction marked as aborted

### 6. Distributed Transaction Coordination

#### Cross-Database Operations
- Single transaction spans both databases
- Two-phase commit protocol (preparing/committing)
- Coordinator ensures consistency across databases
- Failure handling and recovery

#### Example: Order Processing
```sql
-- Financial Database Operations
SELECT FROM accounts WHERE id = payment_account
UPDATE accounts SET balance = balance - total_amount
INSERT INTO transactions (payment record)

-- Inventory Database Operations  
SELECT FROM products WHERE id IN (order_items)
UPDATE products SET stock = stock - quantity
INSERT INTO orders (order record)
INSERT INTO order_items (item records)
UPDATE orders SET status = 'confirmed'
```

## 8 Business Operations Implemented

### 1. Create User
- **Transaction Complexity**: Simple
- **Databases Involved**: Financial
- **Operations**: 1 INSERT

### 2. Create Account
- **Transaction Complexity**: Simple  
- **Databases Involved**: Financial
- **Operations**: 1 SELECT + 1 INSERT

### 3. Transfer Money
- **Transaction Complexity**: Complex
- **Databases Involved**: Financial
- **Operations**: 2 SELECT + 2 UPDATE + 1 INSERT
- **ACID Demo**: Full atomicity - either all operations succeed or all fail

### 4. Deposit Money
- **Transaction Complexity**: Medium
- **Databases Involved**: Financial
- **Operations**: 1 SELECT + 1 UPDATE + 1 INSERT

### 5. Withdraw Money
- **Transaction Complexity**: Medium
- **Databases Involved**: Financial  
- **Operations**: 1 SELECT + 1 UPDATE + 1 INSERT

### 6. Create Product
- **Transaction Complexity**: Simple
- **Databases Involved**: Inventory
- **Operations**: 1 SELECT + 1 INSERT

### 7. Create Order with Payment
- **Transaction Complexity**: Most Complex
- **Databases Involved**: Both (Financial + Inventory)
- **Operations**: 6+ SELECT + 4+ UPDATE + 4+ INSERT
- **Features**: 
  - Cross-database distributed transaction
  - Inventory management
  - Payment processing
  - Order confirmation

### 8. Create Category
- **Transaction Complexity**: Simple
- **Databases Involved**: Inventory
- **Operations**: 1 SELECT + 1 INSERT (if parent category specified)

## Advanced Transaction Scenarios

### Scenario 1: Concurrent Money Transfers
```python
# Multiple threads simultaneously transfer money between same accounts
# System handles conflicts through timestamp ordering
# Automatic restart ensures all transactions complete
```

### Scenario 2: Complex Order Processing
```python
# Single transaction involving:
# - User validation (financial DB)
# - Account balance check (financial DB)  
# - Product availability check (inventory DB)
# - Inventory reduction (inventory DB)
# - Payment processing (financial DB)
# - Order creation (inventory DB)
```

### Scenario 3: Deadlock Resolution
```python
# Two transactions access same resources in different orders
# Wait-for graph detects circular dependency
# Youngest transaction automatically restarted
```

## Usage Examples

### Running the CLI
```bash
cd /path/to/project
python main.py
```

### Running Demonstrations
```bash
# Complete automated demo
python demo.py

# Interactive demo mode
python demo.py --interactive
```

### CLI Commands
```bash
# User operations
python main.py create-user --username john --email john@example.com
python main.py create-account --account-type checking --initial-balance 1000

# Transaction operations
python main.py transfer-money --to-account 2 --amount 100
python main.py deposit-money --amount 500
python main.py withdraw-money --amount 200

# Product operations  
python main.py create-product --name "Laptop" --price 1299.99
python main.py create-order

# System monitoring
python main.py status
python main.py view-accounts
```

## Performance Characteristics

### Concurrency Performance
- Timestamp-based control minimizes lock contention
- Multiversion storage allows concurrent reads
- Automatic restart handles conflicts efficiently

### Scalability Features
- In-memory storage for high-speed operations
- Efficient indexing for fast lookups
- Configurable transaction retry limits
- Performance monitoring and metrics

### Transaction Throughput
- Optimistic concurrency control reduces blocking
- Parallel execution of non-conflicting transactions
- Efficient deadlock detection algorithm

## Testing and Validation

### Concurrency Testing
- Multiple threads executing simultaneous transactions
- Validation of ACID properties under load
- Stress testing of deadlock detection

### Rollback Testing
- Intentional failures to test rollback mechanisms
- Verification of data consistency after rollback
- Complex multi-operation transaction failures

### Distributed Transaction Testing
- Cross-database operation validation
- Network partition simulation (conceptual)
- Two-phase commit protocol verification

## Future Enhancements

### Persistence Layer
- Add disk-based storage for durability
- Implement write-ahead logging (WAL)
- Database recovery mechanisms

### Network Distribution
- TCP/socket-based communication
- Remote database servers
- Network failure handling

### Advanced Concurrency
- Optimistic concurrency control variants
- Lock-based alternatives
- Hybrid approaches

### Monitoring and Administration
- Web-based admin interface
- Real-time performance dashboards
- Transaction debugging tools

## Conclusion

This implementation successfully demonstrates all required features:
- Multi-tier distributed architecture
- Two separate databases with 3+ tables each  
- Complex distributed transactions with ACID properties
- Timestamp-based concurrency control with multiversion support
- Automatic transaction restart mechanism
- Comprehensive rollback system
- Deadlock detection and resolution
- 8+ business operations with varying complexity
- Application-level transaction management (no external framework dependencies)

The system provides a robust foundation for understanding distributed transaction concepts and can serve as a basis for more advanced distributed database systems.