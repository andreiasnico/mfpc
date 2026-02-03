from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

@dataclass
class User:
    """User entity for the system"""
    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'created_at': self.created_at,
            'is_active': self.is_active
        }

@dataclass 
class Account:
    """Bank account entity"""
    id: int
    user_id: int
    account_number: str
    balance: Decimal
    account_type: str  # 'checking', 'savings'
    created_at: datetime
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number': self.account_number,
            'balance': float(self.balance),
            'account_type': self.account_type,
            'created_at': self.created_at,
            'is_active': self.is_active
        }

@dataclass
class Transaction:
    """Transaction record entity"""
    id: int
    from_account_id: Optional[int]
    to_account_id: Optional[int]
    amount: Decimal
    transaction_type: str  # 'transfer', 'deposit', 'withdrawal'
    description: str
    timestamp: datetime
    status: str = 'pending'  # 'pending', 'completed', 'failed'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'from_account_id': self.from_account_id,
            'to_account_id': self.to_account_id,
            'amount': float(self.amount),
            'transaction_type': self.transaction_type,
            'description': self.description,
            'timestamp': self.timestamp,
            'status': self.status
        }

@dataclass
class Product:
    """Product entity for inventory system"""
    id: int
    name: str
    description: str
    price: Decimal
    stock_quantity: int
    category_id: int
    created_at: datetime
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'stock_quantity': self.stock_quantity,
            'category_id': self.category_id,
            'created_at': self.created_at,
            'is_active': self.is_active
        }

@dataclass
class Category:
    """Product category entity"""
    id: int
    name: str
    description: str
    parent_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id
        }

@dataclass
class Order:
    """Order entity"""
    id: int
    user_id: int
    total_amount: Decimal
    status: str  # 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled'
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_amount': float(self.total_amount),
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

@dataclass
class OrderItem:
    """Order item entity"""
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price)
        }