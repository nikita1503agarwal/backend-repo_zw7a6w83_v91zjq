"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- Order -> "order" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in USD")
    category: str = Field("iPhone", description="Product category")
    in_stock: bool = Field(True, description="In stock flag")
    image: Optional[str] = Field(None, description="Primary image URL")
    storage: Optional[str] = Field(None, description="Storage capacity, e.g., 128GB")
    color: Optional[str] = Field(None, description="Color variant")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="ID of the product")
    title: str = Field(..., description="Snapshot of product title")
    price: float = Field(..., ge=0, description="Price at time of purchase")
    quantity: int = Field(1, ge=1, description="Quantity ordered")

class CustomerInfo(BaseModel):
    name: str
    email: EmailStr
    address: str

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    items: List[OrderItem]
    total: float = Field(..., ge=0)
    customer: CustomerInfo
    status: str = Field("processing", description="Order status")

# Note: The Flames database viewer will automatically read these via /schema endpoint if implemented.
