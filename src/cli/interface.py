import click
import sys
import os
from decimal import Decimal
from typing import List, Dict, Any
from tabulate import tabulate
from colorama import Fore, Style, init

# Initialize colorama for colored output
init()

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from business.services import BusinessFacade, BusinessException
from database.inmemory_db import DatabaseManager

class CLIManager:
    """CLI Manager to handle all command line operations"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.business_facade = None
        self.current_user_id = None
        self.current_account_id = None
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the system databases and business layer"""
        try:
            # Initialize databases
            self.db_manager.initialize_system_databases()
            
            # Initialize business layer
            self.business_facade = BusinessFacade(self.db_manager)
            
            # Create sample data
            self._create_sample_data()
            
            self.print_success("System initialized successfully!")
            
        except Exception as e:
            self.print_error(f"Failed to initialize system: {str(e)}")
            sys.exit(1)
    
    def _create_sample_data(self):
        """Create some sample data for testing"""
        try:
            # Create sample categories
            def create_categories(thread_id):
                cat1 = self.business_facade.category_service.create_category(
                    "Electronics", "Electronic products", None, thread_id
                )
                cat2 = self.business_facade.category_service.create_category(
                    "Books", "Books and literature", None, thread_id
                )
                cat3 = self.business_facade.category_service.create_category(
                    "Smartphones", "Mobile phones and accessories", cat1, thread_id
                )
                return [cat1, cat2, cat3]
            
            categories = self.business_facade.execute_with_transaction(create_categories)
            
            # Create sample user and accounts
            def create_user_and_accounts(thread_id):
                user_id = self.business_facade.user_service.create_user(
                    "demo_user", "demo@example.com", "hashed_password", thread_id
                )
                
                account1 = self.business_facade.account_service.create_account(
                    user_id, "checking", Decimal("1000.00"), thread_id
                )
                
                account2 = self.business_facade.account_service.create_account(
                    user_id, "savings", Decimal("5000.00"), thread_id
                )
                
                return user_id, account1, account2
            
            user_id, acc1, acc2 = self.business_facade.execute_with_transaction(create_user_and_accounts)
            
            # Create sample products
            def create_products(thread_id):
                prod1 = self.business_facade.product_service.create_product(
                    "iPhone 15", "Latest Apple smartphone", Decimal("999.99"), 50, categories[2], thread_id
                )
                
                prod2 = self.business_facade.product_service.create_product(
                    "Python Programming Book", "Learn Python programming", Decimal("49.99"), 100, categories[1], thread_id
                )
                
                return [prod1, prod2]
            
            products = self.business_facade.execute_with_transaction(create_products)
            
            # Set default user and account for demo
            self.current_user_id = user_id
            self.current_account_id = acc1
            
        except Exception as e:
            self.print_warning(f"Failed to create sample data: {str(e)}")
    
    def print_success(self, message: str):
        """Print success message in green"""
        click.echo(f"{Fore.GREEN}SUCCESS: {message}{Style.RESET_ALL}")
    
    def print_error(self, message: str):
        """Print error message in red"""
        click.echo(f"{Fore.RED}ERROR: {message}{Style.RESET_ALL}")
    
    def print_warning(self, message: str):
        """Print warning message in yellow"""
        click.echo(f"{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}")
    
    def print_info(self, message: str):
        """Print info message in blue"""
        click.echo(f"{Fore.BLUE}INFO: {message}{Style.RESET_ALL}")
    
    def print_table(self, data: List[Dict[str, Any]], headers: List[str] = None):
        """Print data in table format"""
        if not data:
            self.print_warning("No data to display")
            return
        
        if headers is None:
            headers = list(data[0].keys())
        
        table_data = []
        for item in data:
            row = []
            for header in headers:
                value = item.get(header, "N/A")
                if isinstance(value, float):
                    value = f"{value:.2f}"
                row.append(value)
            table_data.append(row)
        
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

# Create CLI manager instance
cli_manager = CLIManager()

@click.group()
@click.pass_context
def cli(ctx):
    """Distributed Transaction System CLI
    
    A demonstration of distributed transactions with ACID properties,
    timestamp-based concurrency control, and deadlock detection.
    """
    ctx.ensure_object(dict)
    ctx.obj['cli_manager'] = cli_manager

@cli.command()
@click.pass_context
def status(ctx):
    """Show system status and statistics"""
    cli_mgr = ctx.obj['cli_manager']
    
    try:
        # Get transaction statistics
        stats = cli_mgr.business_facade.transaction_manager.get_transaction_statistics()
        
        # Get database statistics
        db_stats = {}
        for db_name in ['financial', 'inventory']:
            db = cli_mgr.db_manager.get_database(db_name)
            db_stats[db_name] = db.get_statistics()
        
        cli_mgr.print_info("=== SYSTEM STATUS ===")
        click.echo(f"Current User ID: {cli_mgr.current_user_id}")
        click.echo(f"Current Account ID: {cli_mgr.current_account_id}")
        click.echo()
        
        cli_mgr.print_info("=== TRANSACTION STATISTICS ===")
        click.echo(f"Active Transactions: {stats['active_transactions']}")
        click.echo(f"Total Transactions: {stats['total_transactions']}")
        click.echo(f"Log Entries: {stats['log_entries']}")
        click.echo(f"Multiversion Resources: {stats['multiversion_resources']}")
        click.echo()
        
        cli_mgr.print_info("=== DATABASE STATISTICS ===")
        for db_name, db_stat in db_stats.items():
            click.echo(f"Database: {db_name}")
            click.echo(f"  Total Operations: {db_stat['total_operations']}")
            click.echo(f"  Tables: {len(db_stat['tables'])}")
            for table_name, table_stat in db_stat['tables'].items():
                click.echo(f"    {table_name}: {table_stat['record_count']} records")
            click.echo()
        
    except Exception as e:
        cli_mgr.print_error(f"Failed to get status: {str(e)}")

@cli.command()
@click.option('--username', prompt='Username', help='Username for the new user')
@click.option('--email', prompt='Email', help='Email address for the new user')
@click.option('--password', prompt='Password', hide_input=True, help='Password for the new user')
@click.pass_context
def create_user(ctx, username, email, password):
    """Create a new user (Operation 1)"""
    cli_mgr = ctx.obj['cli_manager']
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.user_service.create_user(
                username, email, f"hashed_{password}", thread_id
            )
        
        user_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"User created successfully with ID: {user_id}")
        
        # Ask if user wants to switch to this user
        if click.confirm("Switch to this user?"):
            cli_mgr.current_user_id = user_id
            cli_mgr.current_account_id = None
            cli_mgr.print_info(f"Switched to user {user_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to create user: {str(e)}")

@cli.command()
@click.option('--user-id', type=int, help='User ID (default: current user)')
@click.option('--account-type', type=click.Choice(['checking', 'savings']), prompt='Account type')
@click.option('--initial-balance', type=float, prompt='Initial balance')
@click.pass_context
def create_account(ctx, user_id, account_type, initial_balance):
    """Create a new account (Operation 2)"""
    cli_mgr = ctx.obj['cli_manager']
    
    if user_id is None:
        user_id = cli_mgr.current_user_id
    
    if user_id is None:
        cli_mgr.print_error("No user specified and no current user set")
        return
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.account_service.create_account(
                user_id, account_type, Decimal(str(initial_balance)), thread_id
            )
        
        account_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"Account created successfully with ID: {account_id}")
        
        # Ask if user wants to switch to this account
        if click.confirm("Set this as current account?"):
            cli_mgr.current_account_id = account_id
            cli_mgr.print_info(f"Switched to account {account_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to create account: {str(e)}")

@cli.command()
@click.option('--from-account', type=int, help='Source account ID (default: current account)')
@click.option('--to-account', type=int, prompt='Destination account ID')
@click.option('--amount', type=float, prompt='Transfer amount')
@click.option('--description', prompt='Description', default='Transfer')
@click.pass_context
def transfer_money(ctx, from_account, to_account, amount, description):
    """Transfer money between accounts (Operation 3 - Complex Distributed Transaction)"""
    cli_mgr = ctx.obj['cli_manager']
    
    if from_account is None:
        from_account = cli_mgr.current_account_id
    
    if from_account is None:
        cli_mgr.print_error("No source account specified and no current account set")
        return
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.transaction_service.transfer_money(
                from_account, to_account, Decimal(str(amount)), description, thread_id
            )
        
        transaction_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"Money transferred successfully. Transaction ID: {transaction_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to transfer money: {str(e)}")

@cli.command()
@click.option('--account-id', type=int, help='Account ID (default: current account)')
@click.option('--amount', type=float, prompt='Deposit amount')
@click.option('--description', prompt='Description', default='Deposit')
@click.pass_context
def deposit_money(ctx, account_id, amount, description):
    """Deposit money to an account (Operation 4)"""
    cli_mgr = ctx.obj['cli_manager']
    
    if account_id is None:
        account_id = cli_mgr.current_account_id
    
    if account_id is None:
        cli_mgr.print_error("No account specified and no current account set")
        return
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.transaction_service.deposit_money(
                account_id, Decimal(str(amount)), description, thread_id
            )
        
        transaction_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"Money deposited successfully. Transaction ID: {transaction_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to deposit money: {str(e)}")

@cli.command()
@click.option('--account-id', type=int, help='Account ID (default: current account)')
@click.option('--amount', type=float, prompt='Withdrawal amount')
@click.option('--description', prompt='Description', default='Withdrawal')
@click.pass_context
def withdraw_money(ctx, account_id, amount, description):
    """Withdraw money from an account (Operation 5)"""
    cli_mgr = ctx.obj['cli_manager']
    
    if account_id is None:
        account_id = cli_mgr.current_account_id
    
    if account_id is None:
        cli_mgr.print_error("No account specified and no current account set")
        return
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.transaction_service.withdraw_money(
                account_id, Decimal(str(amount)), description, thread_id
            )
        
        transaction_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"Money withdrawn successfully. Transaction ID: {transaction_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to withdraw money: {str(e)}")

@cli.command()
@click.option('--name', prompt='Product name')
@click.option('--description', prompt='Product description')
@click.option('--price', type=float, prompt='Product price')
@click.option('--stock', type=int, prompt='Initial stock quantity')
@click.option('--category-id', type=int, prompt='Category ID')
@click.pass_context
def create_product(ctx, name, description, price, stock, category_id):
    """Create a new product (Operation 6)"""
    cli_mgr = ctx.obj['cli_manager']
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.product_service.create_product(
                name, description, Decimal(str(price)), stock, category_id, thread_id
            )
        
        product_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"Product created successfully with ID: {product_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to create product: {str(e)}")

@cli.command()
@click.option('--user-id', type=int, help='User ID (default: current user)')
@click.option('--payment-account', type=int, help='Payment account ID (default: current account)')
@click.pass_context
def create_order(ctx, user_id, payment_account):
    """Create an order with multiple items (Operation 7 - Most Complex Distributed Transaction)"""
    cli_mgr = ctx.obj['cli_manager']
    
    if user_id is None:
        user_id = cli_mgr.current_user_id
    
    if payment_account is None:
        payment_account = cli_mgr.current_account_id
    
    if user_id is None or payment_account is None:
        cli_mgr.print_error("User ID and payment account must be specified")
        return
    
    # Collect order items
    items = []
    while True:
        click.echo(f"\nAdding item #{len(items) + 1}")
        product_id = click.prompt("Product ID", type=int)
        quantity = click.prompt("Quantity", type=int)
        
        items.append({
            'product_id': product_id,
            'quantity': quantity
        })
        
        if not click.confirm("Add another item?"):
            break
    
    if not items:
        cli_mgr.print_warning("No items specified")
        return
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.order_service.create_order(
                user_id, items, payment_account, thread_id
            )
        
        order_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"Order created successfully with ID: {order_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to create order: {str(e)}")

@cli.command()
@click.option('--name', prompt='Category name')
@click.option('--description', prompt='Category description')
@click.option('--parent-id', type=int, help='Parent category ID (optional)')
@click.pass_context
def create_category(ctx, name, description, parent_id):
    """Create a new product category (Operation 8)"""
    cli_mgr = ctx.obj['cli_manager']
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.category_service.create_category(
                name, description, parent_id, thread_id
            )
        
        category_id = cli_mgr.business_facade.execute_with_transaction(operation)
        cli_mgr.print_success(f"Category created successfully with ID: {category_id}")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to create category: {str(e)}")

@cli.command()
@click.option('--user-id', type=int, help='User ID (default: current user)')
@click.pass_context
def view_accounts(ctx, user_id):
    """View user accounts"""
    cli_mgr = ctx.obj['cli_manager']
    
    if user_id is None:
        user_id = cli_mgr.current_user_id
    
    if user_id is None:
        cli_mgr.print_error("No user specified and no current user set")
        return
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.account_service.get_user_accounts(user_id, thread_id)
        
        accounts = cli_mgr.business_facade.execute_with_transaction(operation)
        
        if accounts:
            cli_mgr.print_info(f"Accounts for User {user_id}:")
            cli_mgr.print_table(accounts, ['id', 'account_number', 'balance', 'account_type', 'is_active'])
        else:
            cli_mgr.print_warning("No accounts found for this user")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to get accounts: {str(e)}")

@cli.command()
@click.pass_context
def view_categories(ctx):
    """View all categories"""
    cli_mgr = ctx.obj['cli_manager']
    
    try:
        def operation(thread_id):
            return cli_mgr.business_facade.category_service.get_all_categories(thread_id)
        
        categories = cli_mgr.business_facade.execute_with_transaction(operation)
        
        if categories:
            cli_mgr.print_info("Product Categories:")
            cli_mgr.print_table(categories, ['id', 'name', 'description', 'parent_id'])
        else:
            cli_mgr.print_warning("No categories found")
        
    except BusinessException as e:
        cli_mgr.print_error(f"Failed to get categories: {str(e)}")

@cli.command()
@click.option('--user-id', type=int, prompt='User ID')
@click.pass_context
def switch_user(ctx, user_id):
    """Switch to a different user"""
    cli_mgr = ctx.obj['cli_manager']
    cli_mgr.current_user_id = user_id
    cli_mgr.current_account_id = None  # Reset account when switching users
    cli_mgr.print_success(f"Switched to user {user_id}")

@cli.command()
@click.option('--account-id', type=int, prompt='Account ID')
@click.pass_context
def switch_account(ctx, account_id):
    """Switch to a different account"""
    cli_mgr = ctx.obj['cli_manager']
    cli_mgr.current_account_id = account_id
    cli_mgr.print_success(f"Switched to account {account_id}")

if __name__ == '__main__':
    cli()