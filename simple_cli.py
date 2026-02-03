#!/usr/bin/env python3
"""
Simple CLI interface with loguru logging
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from business.services import BusinessFacade, BusinessException
from database.inmemory_db import DatabaseManager
from decimal import Decimal
import threading
from loguru import logger

class SimpleCLI:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.business_facade = None
        self.current_user_id = 1
        self.current_account_id = 1
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize system with sample data"""
        logger.info("Initializing Distributed Transaction System...")
        
        self.db_manager.initialize_system_databases()
        self.business_facade = BusinessFacade(self.db_manager)
        
        # Create sample data
        try:
            def create_sample_data(thread_id):
                # Create categories
                cat1 = self.business_facade.category_service.create_category(
                    "Electronics", "Electronic products", None, thread_id
                )
                
                # Create user and accounts
                user_id = self.business_facade.user_service.create_user(
                    "demo_user", "demo@example.com", "hashed_password", thread_id
                )
                
                account1 = self.business_facade.account_service.create_account(
                    user_id, "checking", Decimal("1000.00"), thread_id
                )
                
                account2 = self.business_facade.account_service.create_account(
                    user_id, "savings", Decimal("5000.00"), thread_id
                )
                
                # Create products
                prod1 = self.business_facade.product_service.create_product(
                    "iPhone 15", "Latest smartphone", Decimal("999.99"), 50, cat1, thread_id
                )
                
                return user_id, account1, account2, prod1
            
            user_id, acc1, acc2, prod1 = self.business_facade.execute_with_transaction(create_sample_data)
            self.current_user_id = user_id
            self.current_account_id = acc1
            
            logger.success(f"System initialized with sample data! Demo user ID: {user_id}, Account ID: {acc1}")
            
        except Exception as e:
            logger.warning(f"Could not create sample data: {str(e)}")
        
        print()
    
    def show_help(self):
        """Show available commands"""
        print("Available commands:")
        print("  1 - Show system status")
        print("  2 - Transfer money") 
        print("  3 - Deposit money")
        print("  4 - Withdraw money")
        print("  5 - Create product")
        print("  6 - Create order")
        print("  7 - View accounts")
        print("  8 - Run concurrency test")
        print("  9 - Help")
        print("  0 - Exit")
        print()
    
    def show_status(self):
        """Show system status"""
        stats = self.business_facade.transaction_manager.get_transaction_statistics()
        
        print("=== SYSTEM STATUS ===")
        print(f"Current User ID: {self.current_user_id}")
        print(f"Current Account ID: {self.current_account_id}")
        print()
        print(f"Active Transactions: {stats['active_transactions']}")
        print(f"Total Transactions: {stats['total_transactions']}")
        print(f"Log Entries: {stats['log_entries']}")
        print()
        
        for db_name in ['financial', 'inventory']:
            db = self.db_manager.get_database(db_name)
            db_stats = db.get_statistics()
            print(f"Database '{db_name}':")
            for table_name, table_stats in db_stats['tables'].items():
                print(f"  {table_name}: {table_stats['record_count']} records")
        print()
    
    def transfer_money(self):
        """Transfer money interface"""
        try:
            to_account = int(input("Destination account ID: "))
            amount = float(input("Amount: "))
            description = input("Description (optional): ") or "Transfer"
            
            def operation(thread_id):
                return self.business_facade.transaction_service.transfer_money(
                    self.current_account_id, to_account, Decimal(str(amount)), description, thread_id
                )
            
            tx_id = self.business_facade.execute_with_transaction(operation)
            print(f"Transfer completed! Transaction ID: {tx_id}")
            logger.info(f"Money transfer successful - TX:{tx_id} - Amount:{amount} - From:{self.current_account_id} - To:{to_account}")
            
        except Exception as e:
            print(f"Transfer failed: {str(e)}")
            logger.error(f"Money transfer failed: {str(e)}")
        print()
    
    def deposit_money(self):
        """Deposit money interface"""
        try:
            amount = float(input("Deposit amount: "))
            description = input("Description (optional): ") or "Deposit"
            
            def operation(thread_id):
                return self.business_facade.transaction_service.deposit_money(
                    self.current_account_id, Decimal(str(amount)), description, thread_id
                )
            
            tx_id = self.business_facade.execute_with_transaction(operation)
            print(f"Deposit completed! Transaction ID: {tx_id}")
            logger.info(f"Deposit successful - TX:{tx_id} - Amount:{amount} - Account:{self.current_account_id}")
            
        except Exception as e:
            print(f"Deposit failed: {str(e)}")
            logger.error(f"Deposit failed: {str(e)}")
        print()
    
    def withdraw_money(self):
        """Withdraw money interface"""
        try:
            amount = float(input("Withdrawal amount: "))
            description = input("Description (optional): ") or "Withdrawal"
            
            def operation(thread_id):
                return self.business_facade.transaction_service.withdraw_money(
                    self.current_account_id, Decimal(str(amount)), description, thread_id
                )
            
            tx_id = self.business_facade.execute_with_transaction(operation)
            print(f"Withdrawal completed! Transaction ID: {tx_id}")
            logger.info(f"Withdrawal successful - TX:{tx_id} - Amount:{amount} - Account:{self.current_account_id}")
            
        except Exception as e:
            print(f"Withdrawal failed: {str(e)}")
            logger.error(f"Withdrawal failed: {str(e)}")
        print()
    
    def create_product(self):
        """Create product interface"""
        try:
            name = input("Product name: ")
            description = input("Product description: ")
            price = float(input("Product price: "))
            stock = int(input("Initial stock: "))
            category_id = int(input("Category ID: "))
            
            def operation(thread_id):
                return self.business_facade.product_service.create_product(
                    name, description, Decimal(str(price)), stock, category_id, thread_id
                )
            
            prod_id = self.business_facade.execute_with_transaction(operation)
            print(f"Product created! Product ID: {prod_id}")
            logger.info(f"Product created successfully - ID:{prod_id} - Name:{name}")
            
        except Exception as e:
            print(f"Product creation failed: {str(e)}")
            logger.error(f"Product creation failed: {str(e)}")
        print()
    
    def create_order(self):
        """Create order interface"""
        try:
            print("Creating order...")
            items = []
            
            while True:
                prod_id = int(input("Product ID: "))
                quantity = int(input("Quantity: "))
                items.append({'product_id': prod_id, 'quantity': quantity})
                
                more = input("Add more items? (y/n): ").lower()
                if more != 'y':
                    break
            
            def operation(thread_id):
                return self.business_facade.order_service.create_order(
                    self.current_user_id, items, self.current_account_id, thread_id
                )
            
            order_id = self.business_facade.execute_with_transaction(operation)
            print(f"Order created! Order ID: {order_id}")
            logger.info(f"Order created successfully - ID:{order_id} - User:{self.current_user_id} - Items:{len(items)}")
            
        except Exception as e:
            print(f"Order creation failed: {str(e)}")
            logger.error(f"Order creation failed: {str(e)}")
        print()
    
    def view_accounts(self):
        """View user accounts"""
        try:
            def operation(thread_id):
                return self.business_facade.account_service.get_user_accounts(
                    self.current_user_id, thread_id
                )
            
            accounts = self.business_facade.execute_with_transaction(operation)
            
            if accounts:
                print("User Accounts:")
                for acc in accounts:
                    print(f"  ID: {acc['id']}, Type: {acc['account_type']}, "
                          f"Balance: ${acc['balance']:.2f}")
            else:
                print("No accounts found")
                
        except Exception as e:
            print(f"Failed to get accounts: {str(e)}")
            logger.error(f"Failed to get accounts: {str(e)}")
        print()
    
    def run_concurrency_test(self):
        """Test concurrency with multiple threads"""
        print("Running concurrency test with 5 concurrent transfers...")
        
        results = []
        errors = []
        
        def concurrent_transfer(thread_num, result_list, error_list):
            try:
                def transfer_op(thread_id):
                    return self.business_facade.transaction_service.transfer_money(
                        self.current_account_id, 2, Decimal("10.00"), 
                        f"Concurrent transfer {thread_num}", thread_id
                    )
                
                tx_id = self.business_facade.execute_with_transaction(transfer_op)
                result_list.append(f"Thread {thread_num}: Success (TX: {tx_id})")
                
            except Exception as e:
                error_list.append(f"Thread {thread_num}: {str(e)}")
        
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=concurrent_transfer,
                args=(i+1, results, errors)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        print("Results:")
        for result in results:
            print(f"  SUCCESS: {result}")
            logger.info(f"Concurrent operation result: {result}")
        
        for error in errors:
            print(f"  WARNING: {error}")
            logger.warning(f"Concurrent operation error: {error}")
        
        print()
    
    def run(self):
        """Main CLI loop"""
        print("Welcome to the Distributed Transaction System!")
        print("Type '9' for help or '0' to exit.")
        print()
        
        while True:
            try:
                command = input("DTS> ").strip()
                
                if command == '0':
                    print("Goodbye!")
                    break
                elif command == '1':
                    self.show_status()
                elif command == '2':
                    self.transfer_money()
                elif command == '3':
                    self.deposit_money()
                elif command == '4':
                    self.withdraw_money()
                elif command == '5':
                    self.create_product()
                elif command == '6':
                    self.create_order()
                elif command == '7':
                    self.view_accounts()
                elif command == '8':
                    self.run_concurrency_test()
                elif command == '9':
                    self.show_help()
                else:
                    print("Unknown command. Type '9' for help.")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == 'demo':
        # Run automated demo
        os.system(f"cd {os.path.dirname(__file__)} && PYTHONPATH={os.path.dirname(__file__)}/src python demo.py")
    else:
        # Run interactive CLI
        cli = SimpleCLI()
        cli.run()

if __name__ == '__main__':
    main()