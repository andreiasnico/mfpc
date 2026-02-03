# Distributed Transaction System

A Python implementation of a distributed transactional system with in-memory databases, supporting ACID properties, concurrency control, and deadlock detection.

## Features

- Multi-tier architecture (CLI - Business Logic - Data Layer)
- Two in-memory databases with 3+ tables each
- Distributed transactions with ACID properties
- Timestamp-based concurrency control with multiversion support
- Automatic transaction restart on abort
- Rollback mechanisms
- Deadlock detection and resolution
- 8 business operations/use cases

## Architecture

```
CLI Interface
    ↓
Business Layer (Middleware)
    ↓
Transaction Manager
    ↓
Database Layer (2 In-Memory DBs)
```

## Installation

```bash
pip install loguru
```

## Usage

```bash
python main.py
```

## Project Structure

- `main.py` - CLI interface entry point
- `cli/` - Command line interface module
- `business/` - Business logic and middleware layer
- `transaction/` - Transaction management system
- `database/` - In-memory database implementations
- `models/` - Data models and entities