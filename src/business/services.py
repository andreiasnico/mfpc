from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime
import threading

from transaction.manager import TransactionManager, TransactionException
from models.entities import User, Account, Transaction as TransactionRecord, Product, Category, Order, OrderItem
from database.inmemory_db import DatabaseManager

class BusinessException(Exception):
    """Business logic related exceptions"""
    pass

class UserService:
    """User management service"""
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
    
    def create_user(self, username: str, email: str, password_hash: str, thread_id: str) -> int:
        """Create a new user"""
        try:
            user_data = {
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'created_at': datetime.now(),
                'is_active': True
            }
            
            # Check if user already exists
            existing_users = self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'financial', 'users'
            )
            
            if existing_users:
                for user in existing_users:
                    if user['username'] == username or user['email'] == email:
                        raise BusinessException("User with this username or email already exists")
            
            user_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'financial', 'users', data=user_data
            )
            
            return user_id
            
        except Exception as e:
            raise BusinessException(f"Failed to create user: {str(e)}")
    
    def get_user(self, user_id: int, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            return self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'financial', 'users', record_id=user_id
            )
        except Exception as e:
            raise BusinessException(f"Failed to get user: {str(e)}")
    
    def update_user(self, user_id: int, updates: Dict[str, Any], thread_id: str) -> bool:
        """Update user information"""
        try:
            return self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'financial', 'users', record_id=user_id, data=updates
            )
        except Exception as e:
            raise BusinessException(f"Failed to update user: {str(e)}")

class AccountService:
    """Account management service"""
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
    
    def create_account(self, user_id: int, account_type: str, initial_balance: Decimal, thread_id: str) -> int:
        """Create a new account"""
        try:
            # Verify user exists
            user = self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'financial', 'users', record_id=user_id
            )
            
            if not user:
                raise BusinessException("User does not exist")
            
            account_number = f"ACC{user_id}{int(datetime.now().timestamp())}"
            
            account_data = {
                'user_id': user_id,
                'account_number': account_number,
                'balance': float(initial_balance),
                'account_type': account_type,
                'created_at': datetime.now(),
                'is_active': True
            }
            
            account_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'financial', 'accounts', data=account_data
            )
            
            return account_id
            
        except Exception as e:
            raise BusinessException(f"Failed to create account: {str(e)}")
    
    def get_account(self, account_id: int, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID"""
        try:
            return self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'financial', 'accounts', record_id=account_id
            )
        except Exception as e:
            raise BusinessException(f"Failed to get account: {str(e)}")
    
    def get_user_accounts(self, user_id: int, thread_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a user"""
        try:
            all_accounts = self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'financial', 'accounts'
            )
            
            if not all_accounts:
                return []
            
            return [account for account in all_accounts if account['user_id'] == user_id]
            
        except Exception as e:
            raise BusinessException(f"Failed to get user accounts: {str(e)}")

class TransactionService:
    """Transaction/Payment service"""
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
        self.account_service = AccountService(transaction_manager)
    
    def transfer_money(self, from_account_id: int, to_account_id: int, 
                      amount: Decimal, description: str, thread_id: str) -> int:
        """Transfer money between accounts (distributed transaction)"""
        try:
            # This is our distributed transaction across multiple operations
            
            # 1. SELECT: Verify source account exists and has sufficient funds
            from_account = self.account_service.get_account(from_account_id, thread_id)
            if not from_account:
                raise BusinessException("Source account does not exist")
            
            if Decimal(str(from_account['balance'])) < amount:
                raise BusinessException("Insufficient funds")
            
            # 2. SELECT: Verify destination account exists
            to_account = self.account_service.get_account(to_account_id, thread_id)
            if not to_account:
                raise BusinessException("Destination account does not exist")
            
            # 3. UPDATE: Debit source account
            new_from_balance = Decimal(str(from_account['balance'])) - amount
            self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'financial', 'accounts', 
                record_id=from_account_id,
                data={'balance': float(new_from_balance)}
            )
            
            # 4. UPDATE: Credit destination account
            new_to_balance = Decimal(str(to_account['balance'])) + amount
            self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'financial', 'accounts',
                record_id=to_account_id,
                data={'balance': float(new_to_balance)}
            )
            
            # 5. INSERT: Record the transaction
            transaction_data = {
                'from_account_id': from_account_id,
                'to_account_id': to_account_id,
                'amount': float(amount),
                'transaction_type': 'transfer',
                'description': description,
                'timestamp': datetime.now(),
                'status': 'completed'
            }
            
            transaction_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'financial', 'transactions', data=transaction_data
            )
            
            return transaction_id
            
        except Exception as e:
            raise BusinessException(f"Failed to transfer money: {str(e)}")
    
    def deposit_money(self, account_id: int, amount: Decimal, description: str, thread_id: str) -> int:
        """Deposit money to an account"""
        try:
            # 1. SELECT: Verify account exists
            account = self.account_service.get_account(account_id, thread_id)
            if not account:
                raise BusinessException("Account does not exist")
            
            # 2. UPDATE: Credit account
            new_balance = Decimal(str(account['balance'])) + amount
            self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'financial', 'accounts',
                record_id=account_id,
                data={'balance': float(new_balance)}
            )
            
            # 3. INSERT: Record the transaction
            transaction_data = {
                'from_account_id': None,
                'to_account_id': account_id,
                'amount': float(amount),
                'transaction_type': 'deposit',
                'description': description,
                'timestamp': datetime.now(),
                'status': 'completed'
            }
            
            transaction_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'financial', 'transactions', data=transaction_data
            )
            
            return transaction_id
            
        except Exception as e:
            raise BusinessException(f"Failed to deposit money: {str(e)}")
    
    def withdraw_money(self, account_id: int, amount: Decimal, description: str, thread_id: str) -> int:
        """Withdraw money from an account"""
        try:
            # 1. SELECT: Verify account exists and has sufficient funds
            account = self.account_service.get_account(account_id, thread_id)
            if not account:
                raise BusinessException("Account does not exist")
            
            if Decimal(str(account['balance'])) < amount:
                raise BusinessException("Insufficient funds")
            
            # 2. UPDATE: Debit account
            new_balance = Decimal(str(account['balance'])) - amount
            self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'financial', 'accounts',
                record_id=account_id,
                data={'balance': float(new_balance)}
            )
            
            # 3. INSERT: Record the transaction
            transaction_data = {
                'from_account_id': account_id,
                'to_account_id': None,
                'amount': float(amount),
                'transaction_type': 'withdrawal',
                'description': description,
                'timestamp': datetime.now(),
                'status': 'completed'
            }
            
            transaction_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'financial', 'transactions', data=transaction_data
            )
            
            return transaction_id
            
        except Exception as e:
            raise BusinessException(f"Failed to withdraw money: {str(e)}")

class ProductService:
    """Product management service"""
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
    
    def create_product(self, name: str, description: str, price: Decimal, 
                      stock_quantity: int, category_id: int, thread_id: str) -> int:
        """Create a new product"""
        try:
            # Verify category exists
            category = self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'inventory', 'categories', record_id=category_id
            )
            
            if not category:
                raise BusinessException("Category does not exist")
            
            product_data = {
                'name': name,
                'description': description,
                'price': float(price),
                'stock_quantity': stock_quantity,
                'category_id': category_id,
                'created_at': datetime.now(),
                'is_active': True
            }
            
            product_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'inventory', 'products', data=product_data
            )
            
            return product_id
            
        except Exception as e:
            raise BusinessException(f"Failed to create product: {str(e)}")
    
    def update_stock(self, product_id: int, quantity_change: int, thread_id: str) -> bool:
        """Update product stock quantity"""
        try:
            # 1. SELECT: Get current product
            product = self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'inventory', 'products', record_id=product_id
            )
            
            if not product:
                raise BusinessException("Product does not exist")
            
            new_quantity = product['stock_quantity'] + quantity_change
            if new_quantity < 0:
                raise BusinessException("Insufficient stock")
            
            # 2. UPDATE: Update stock quantity
            return self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'inventory', 'products',
                record_id=product_id,
                data={'stock_quantity': new_quantity}
            )
            
        except Exception as e:
            raise BusinessException(f"Failed to update stock: {str(e)}")

class OrderService:
    """Order management service"""
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
        self.product_service = ProductService(transaction_manager)
        self.transaction_service = TransactionService(transaction_manager)
    
    def create_order(self, user_id: int, items: List[Dict[str, Any]], 
                    payment_account_id: int, thread_id: str) -> int:
        """Create an order with payment (complex distributed transaction)"""
        try:
            # This is our most complex distributed transaction involving both databases
            
            total_amount = Decimal('0')
            
            # 1. SELECT: Verify user exists
            user = self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'financial', 'users', record_id=user_id
            )
            if not user:
                raise BusinessException("User does not exist")
            
            # 2. SELECT: Verify payment account exists and get balance
            payment_account = self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'financial', 'accounts', record_id=payment_account_id
            )
            if not payment_account:
                raise BusinessException("Payment account does not exist")
            
            # 3. Validate items and calculate total
            validated_items = []
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                # SELECT: Get product details
                product = self.transaction_manager.execute_operation(
                    thread_id, 'SELECT', 'inventory', 'products', record_id=product_id
                )
                
                if not product:
                    raise BusinessException(f"Product {product_id} does not exist")
                
                if product['stock_quantity'] < quantity:
                    raise BusinessException(f"Insufficient stock for product {product['name']}")
                
                unit_price = Decimal(str(product['price']))
                item_total = unit_price * quantity
                total_amount += item_total
                
                validated_items.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': item_total,
                    'current_stock': product['stock_quantity']
                })
            
            # 4. Check if payment account has sufficient funds
            if Decimal(str(payment_account['balance'])) < total_amount:
                raise BusinessException("Insufficient funds for payment")
            
            # 5. INSERT: Create order
            order_data = {
                'user_id': user_id,
                'total_amount': float(total_amount),
                'status': 'pending',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            order_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'inventory', 'orders', data=order_data
            )
            
            # 6. INSERT: Create order items and UPDATE: Reduce stock
            for item in validated_items:
                # Insert order item
                order_item_data = {
                    'order_id': order_id,
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'unit_price': float(item['unit_price']),
                    'total_price': float(item['total_price'])
                }
                
                self.transaction_manager.execute_operation(
                    thread_id, 'INSERT', 'inventory', 'order_items', data=order_item_data
                )
                
                # Update product stock
                new_stock = item['current_stock'] - item['quantity']
                self.transaction_manager.execute_operation(
                    thread_id, 'UPDATE', 'inventory', 'products',
                    record_id=item['product_id'],
                    data={'stock_quantity': new_stock}
                )
            
            # 7. UPDATE: Process payment (deduct from account)
            new_balance = Decimal(str(payment_account['balance'])) - total_amount
            self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'financial', 'accounts',
                record_id=payment_account_id,
                data={'balance': float(new_balance)}
            )
            
            # 8. INSERT: Record payment transaction
            payment_data = {
                'from_account_id': payment_account_id,
                'to_account_id': None,
                'amount': float(total_amount),
                'transaction_type': 'payment',
                'description': f'Payment for order {order_id}',
                'timestamp': datetime.now(),
                'status': 'completed'
            }
            
            self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'financial', 'transactions', data=payment_data
            )
            
            # 9. UPDATE: Confirm order
            self.transaction_manager.execute_operation(
                thread_id, 'UPDATE', 'inventory', 'orders',
                record_id=order_id,
                data={'status': 'confirmed', 'updated_at': datetime.now()}
            )
            
            return order_id
            
        except Exception as e:
            raise BusinessException(f"Failed to create order: {str(e)}")

class CategoryService:
    """Category management service"""
    
    def __init__(self, transaction_manager: TransactionManager):
        self.transaction_manager = transaction_manager
    
    def create_category(self, name: str, description: str, parent_id: Optional[int], thread_id: str) -> int:
        """Create a new category"""
        try:
            if parent_id is not None:
                # Verify parent category exists
                parent = self.transaction_manager.execute_operation(
                    thread_id, 'SELECT', 'inventory', 'categories', record_id=parent_id
                )
                if not parent:
                    raise BusinessException("Parent category does not exist")
            
            category_data = {
                'name': name,
                'description': description,
                'parent_id': parent_id
            }
            
            category_id = self.transaction_manager.execute_operation(
                thread_id, 'INSERT', 'inventory', 'categories', data=category_data
            )
            
            return category_id
            
        except Exception as e:
            raise BusinessException(f"Failed to create category: {str(e)}")
    
    def get_all_categories(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all categories"""
        try:
            return self.transaction_manager.execute_operation(
                thread_id, 'SELECT', 'inventory', 'categories'
            ) or []
        except Exception as e:
            raise BusinessException(f"Failed to get categories: {str(e)}")

class BusinessFacade:
    """Main business facade providing unified access to all services"""
    
    def __init__(self, database_manager: DatabaseManager):
        self.transaction_manager = TransactionManager(database_manager)
        self.user_service = UserService(self.transaction_manager)
        self.account_service = AccountService(self.transaction_manager)
        self.transaction_service = TransactionService(self.transaction_manager)
        self.product_service = ProductService(self.transaction_manager)
        self.order_service = OrderService(self.transaction_manager)
        self.category_service = CategoryService(self.transaction_manager)
    
    def execute_with_transaction(self, operation: callable, thread_id: str = None, max_retries: int = 3) -> Any:
        """Execute an operation within a transaction with automatic retry on restart"""
        if thread_id is None:
            thread_id = str(threading.current_thread().ident)
        
        for attempt in range(max_retries):
            try:
                # Begin transaction
                transaction_id = self.transaction_manager.begin_transaction(thread_id)
                
                # Execute operation
                result = operation(thread_id)
                
                # Commit transaction
                self.transaction_manager.commit_transaction(thread_id)
                
                return result
                
            except TransactionException as e:
                if "restarted" in str(e) and attempt < max_retries - 1:
                    # Transaction was restarted, retry
                    continue
                else:
                    # Final attempt or non-restart error
                    try:
                        self.transaction_manager.rollback_transaction(thread_id)
                    except:
                        pass
                    raise BusinessException(f"Transaction failed after {attempt + 1} attempts: {str(e)}")
            except Exception as e:
                # Rollback on any other error
                try:
                    self.transaction_manager.rollback_transaction(thread_id)
                except:
                    pass
                raise BusinessException(f"Operation failed: {str(e)}")
        
        raise BusinessException(f"Transaction failed after {max_retries} attempts")