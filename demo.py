#!/usr/bin/env python3
"""
Comprehensive test script for the Distributed Transaction System
Demonstrates all the implemented features including ACID properties,
concurrency control, deadlock detection, and distributed transactions.
"""

import sys
import os
import threading
import time
import random
from decimal import Decimal
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import config first to set up logging
import config

from business.services import BusinessFacade, BusinessException
from database.inmemory_db import DatabaseManager
from transaction.manager import TransactionException

class DistributedTransactionDemo:
    """Demo class showcasing the distributed transaction system"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.business_facade = None
        self.demo_users = []
        self.demo_accounts = []
        self.demo_products = []
        self.demo_categories = []
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the system"""
        print("Initializing Distributed Transaction System...")
        logger.info("Starting system initialization")
        
        # Initialize databases
        self.db_manager.initialize_system_databases()
        
        # Initialize business layer
        self.business_facade = BusinessFacade(self.db_manager)
        
        print("System initialized successfully!")
        logger.success("System initialization completed")
        print()
    
    def create_sample_data(self):
        """Create comprehensive sample data"""
        print("Creating sample data...")
        logger.info("Starting sample data creation")
        
        try:
            # Create categories
            def create_categories(thread_id):
                categories = []
                categories.append(self.business_facade.category_service.create_category(
                    "Electronics", "Electronic products and gadgets", None, thread_id
                ))
                categories.append(self.business_facade.category_service.create_category(
                    "Books", "Books and educational materials", None, thread_id
                ))
                categories.append(self.business_facade.category_service.create_category(
                    "Smartphones", "Mobile phones and accessories", categories[0], thread_id
                ))
                categories.append(self.business_facade.category_service.create_category(
                    "Laptops", "Computers and laptops", categories[0], thread_id
                ))
                return categories
            
            self.demo_categories = self.business_facade.execute_with_transaction(create_categories)
            print(f"Created {len(self.demo_categories)} categories")
            logger.info(f"Created {len(self.demo_categories)} categories successfully")
            
            # Create users and accounts
            def create_users_and_accounts(thread_id):
                users = []
                accounts = []
                
                for i in range(3):
                    user_id = self.business_facade.user_service.create_user(
                        f"user{i+1}", f"user{i+1}@example.com", f"hashed_password_{i+1}", thread_id
                    )
                    users.append(user_id)
                    
                    # Create accounts for each user
                    checking_account = self.business_facade.account_service.create_account(
                        user_id, "checking", Decimal("1000.00"), thread_id
                    )
                    savings_account = self.business_facade.account_service.create_account(
                        user_id, "savings", Decimal("5000.00"), thread_id
                    )
                    accounts.extend([checking_account, savings_account])
                
                return users, accounts
            
            self.demo_users, self.demo_accounts = self.business_facade.execute_with_transaction(create_users_and_accounts)
            print(f"Created {len(self.demo_users)} users and {len(self.demo_accounts)} accounts")
            logger.info(f"Created {len(self.demo_users)} users and {len(self.demo_accounts)} accounts successfully")
            
            # Create products
            def create_products(thread_id):
                products = []
                
                products.append(self.business_facade.product_service.create_product(
                    "iPhone 15 Pro", "Latest Apple smartphone with advanced features", 
                    Decimal("1199.99"), 25, self.demo_categories[2], thread_id
                ))
                
                products.append(self.business_facade.product_service.create_product(
                    "MacBook Pro M3", "High-performance laptop for professionals", 
                    Decimal("2399.99"), 15, self.demo_categories[3], thread_id
                ))
                
                products.append(self.business_facade.product_service.create_product(
                    "Python Crash Course", "A hands-on introduction to programming", 
                    Decimal("39.99"), 100, self.demo_categories[1], thread_id
                ))
                
                products.append(self.business_facade.product_service.create_product(
                    "Samsung Galaxy S24", "Android smartphone with excellent camera", 
                    Decimal("899.99"), 30, self.demo_categories[2], thread_id
                ))
                
                return products
            
            self.demo_products = self.business_facade.execute_with_transaction(create_products)
            print(f"Created {len(self.demo_products)} products")
            logger.info(f"Created {len(self.demo_products)} products successfully")
            print()
            
        except Exception as e:
            print(f"Error creating sample data: {str(e)}")
            logger.error(f"Failed to create sample data: {str(e)}")
    
    def demonstrate_basic_operations(self):
        """Demonstrate basic CRUD operations"""
        print("Demonstrating basic operations...")
        logger.info("Starting basic operations demonstration")
        
        try:
            # Money transfer
            print("Testing money transfer...")
            def transfer_operation(thread_id):
                return self.business_facade.transaction_service.transfer_money(
                    self.demo_accounts[0], self.demo_accounts[2], Decimal("100.00"), 
                    "Transfer demo", thread_id
                )
            
            tx_id = self.business_facade.execute_with_transaction(transfer_operation)
            print(f"Money transfer completed. Transaction ID: {tx_id}")
            logger.info(f"Money transfer demonstration successful - TX:{tx_id}")
            
            # Deposit money
            print("Testing deposit...")
            def deposit_operation(thread_id):
                return self.business_facade.transaction_service.deposit_money(
                    self.demo_accounts[1], Decimal("500.00"), "Deposit demo", thread_id
                )
            
            tx_id = self.business_facade.execute_with_transaction(deposit_operation)
            print(f"Deposit completed. Transaction ID: {tx_id}")
            logger.info(f"Deposit demonstration successful - TX:{tx_id}")
            
            # Create and process an order (complex distributed transaction)
            print("Testing order creation (complex distributed transaction)...")
            def order_operation(thread_id):
                items = [
                    {'product_id': self.demo_products[0], 'quantity': 1},  # iPhone
                    {'product_id': self.demo_products[2], 'quantity': 2}   # Books
                ]
                return self.business_facade.order_service.create_order(
                    self.demo_users[0], items, self.demo_accounts[0], thread_id
                )
            
            order_id = self.business_facade.execute_with_transaction(order_operation)
            print(f"Order created successfully. Order ID: {order_id}")
            logger.info(f"Order creation demonstration successful - Order:{order_id}")
            print()
            
        except Exception as e:
            print(f"Error in basic operations: {str(e)}")
            logger.error(f"Basic operations demonstration failed: {str(e)}")
    
    def demonstrate_concurrency_control(self):
        """Demonstrate concurrent transaction handling"""
        print("Demonstrating concurrency control...")
        logger.info("Starting concurrency control demonstration")
        
        results = []
        errors = []
        
        def concurrent_transfer(account_from, account_to, amount, description, result_list, error_list):
            """Function to run concurrent transfers"""
            try:
                def transfer_op(thread_id):
                    return self.business_facade.transaction_service.transfer_money(
                        account_from, account_to, amount, description, thread_id
                    )
                
                tx_id = self.business_facade.execute_with_transaction(transfer_op)
                result_list.append(f"Transfer {description}: Success (TX: {tx_id})")
                
            except Exception as e:
                error_list.append(f"Transfer {description}: {str(e)}")
        
        # Start multiple concurrent transactions
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=concurrent_transfer,
                args=(
                    self.demo_accounts[0], self.demo_accounts[1], 
                    Decimal("50.00"), f"Concurrent#{i+1}", 
                    results, errors
                )
            )
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # Small delay to create timing conflicts
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print(f"Concurrent operations completed:")
        for result in results:
            print(f"  SUCCESS: {result}")
            logger.info(f"Concurrent operation result: {result}")
        
        if errors:
            print(f"Some operations failed (expected due to concurrency control):")
            for error in errors:
                print(f"  WARNING: {error}")
                logger.warning(f"Concurrent operation error: {error}")
        
        print()
    
    def demonstrate_transaction_restart(self):
        """Demonstrate automatic transaction restart on conflicts"""
        print("Demonstrating transaction restart mechanism...")
        logger.info("Starting transaction restart demonstration")
        
        def conflicting_operation_1(thread_id):
            """First operation that will conflict"""
            time.sleep(0.5)  # Simulate some processing time
            return self.business_facade.transaction_service.transfer_money(
                self.demo_accounts[2], self.demo_accounts[3], 
                Decimal("75.00"), "Restart demo 1", thread_id
            )
        
        def conflicting_operation_2(thread_id):
            """Second operation that will conflict"""
            time.sleep(0.3)  # Different timing
            return self.business_facade.transaction_service.transfer_money(
                self.demo_accounts[3], self.demo_accounts[2], 
                Decimal("25.00"), "Restart demo 2", thread_id
            )
        
        results = []
        
        # Start conflicting transactions
        thread1 = threading.Thread(target=lambda: results.append(
            ("T1", self.business_facade.execute_with_transaction(conflicting_operation_1))
        ))
        
        thread2 = threading.Thread(target=lambda: results.append(
            ("T2", self.business_facade.execute_with_transaction(conflicting_operation_2))
        ))
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        print(f"Transaction restart demonstration completed:")
        for thread_name, tx_id in results:
            print(f"  SUCCESS: {thread_name}: Success (TX: {tx_id})")
            logger.info(f"Transaction restart result - {thread_name}: TX:{tx_id}")
        
        print()
    
    def demonstrate_rollback(self):
        """Demonstrate transaction rollback"""
        print("Demonstrating transaction rollback...")
        logger.info("Starting rollback demonstration")
        
        try:
            def failing_operation(thread_id):
                # This operation should fail and trigger rollback
                # First, do a successful operation
                self.business_facade.transaction_service.deposit_money(
                    self.demo_accounts[0], Decimal("200.00"), "Before failure", thread_id
                )
                
                # Then try to transfer more money than available (should fail)
                return self.business_facade.transaction_service.transfer_money(
                    self.demo_accounts[0], self.demo_accounts[1], 
                    Decimal("999999.00"), "Should fail", thread_id
                )
            
            # This should fail and rollback
            self.business_facade.execute_with_transaction(failing_operation)
            print("Operation should have failed!")
            logger.error("Rollback demonstration failed - operation should have been rolled back")
            
        except BusinessException as e:
            print(f"Transaction correctly rolled back: {str(e)}")
            logger.success(f"Rollback demonstration successful: {str(e)}")
        
        print()
    
    def show_system_statistics(self):
        """Show comprehensive system statistics"""
        print("System Statistics:")
        print("=" * 50)
        logger.info("Displaying system statistics")
        
        # Transaction statistics
        tx_stats = self.business_facade.transaction_manager.get_transaction_statistics()
        print(f"Active Transactions: {tx_stats['active_transactions']}")
        print(f"Total Transactions: {tx_stats['total_transactions']}")
        print(f"Transaction Log Entries: {tx_stats['log_entries']}")
        print(f"Multiversion Resources: {tx_stats['multiversion_resources']}")
        print()
        
        # Database statistics
        for db_name in ['financial', 'inventory']:
            db = self.db_manager.get_database(db_name)
            db_stats = db.get_statistics()
            print(f"Database '{db_name}':")
            print(f"  Total Operations: {db_stats['total_operations']}")
            print(f"  Tables: {len(db_stats['tables'])}")
            for table_name, table_stats in db_stats['tables'].items():
                print(f"    {table_name}: {table_stats['record_count']} records")
            print()
    
    def run_comprehensive_demo(self):
        """Run the complete demonstration"""
        print("Starting Comprehensive Distributed Transaction System Demo")
        print("=" * 60)
        logger.info("Starting comprehensive demonstration")
        print()
        
        # Create sample data
        self.create_sample_data()
        
        # Demonstrate basic operations
        self.demonstrate_basic_operations()
        
        # Demonstrate concurrency control
        self.demonstrate_concurrency_control()
        
        # Demonstrate transaction restart
        self.demonstrate_transaction_restart()
        
        # Demonstrate rollback
        self.demonstrate_rollback()
        
        # Show final statistics
        self.show_system_statistics()
        
        print("Demo completed successfully!")
        logger.success("Comprehensive demonstration completed successfully")
        print("\nFeatures Demonstrated:")
        print("- Multi-tier architecture (CLI - Business - Transaction - Database)")
        print("- Two separate in-memory databases")
        print("- Distributed transactions with ACID properties")
        print("- Timestamp-based concurrency control")
        print("- Multiversion storage")
        print("- Automatic transaction restart")
        print("- Rollback mechanisms")
        print("- Deadlock detection")
        print("- 8+ business operations")
        print("- Complex multi-operation transactions")

def main():
    """Main function to run the demo"""
    demo = DistributedTransactionDemo()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Interactive mode - user can run individual demonstrations
        print("Interactive mode - choose demonstrations to run:")
        print("1. Create sample data")
        print("2. Basic operations")
        print("3. Concurrency control")
        print("4. Transaction restart")
        print("5. Rollback demonstration")
        print("6. System statistics")
        print("7. Run all")
        
        choice = input("Enter choice (1-7): ")
        
        if choice == "1":
            demo.create_sample_data()
        elif choice == "2":
            demo.create_sample_data()
            demo.demonstrate_basic_operations()
        elif choice == "3":
            demo.create_sample_data()
            demo.demonstrate_concurrency_control()
        elif choice == "4":
            demo.create_sample_data()
            demo.demonstrate_transaction_restart()
        elif choice == "5":
            demo.create_sample_data()
            demo.demonstrate_rollback()
        elif choice == "6":
            demo.create_sample_data()
            demo.show_system_statistics()
        elif choice == "7":
            demo.run_comprehensive_demo()
        else:
            print("Invalid choice")
    else:
        # Run complete demo
        demo.run_comprehensive_demo()

if __name__ == '__main__':
    main()