"""Auto-generated Pydantic models from ontology."""

from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime


class Person(BaseModel):
    """A person entity"""
    name: str: Field(description="Full name of the person")
    age: int: Field(description="Age of the person", ge=0.0, le=150.0)
    email: str: Field(description="Email address", default=None)
    status: str: Field(description="Current status", enum=['active', 'inactive', 'pending'])

class Product(BaseModel):
    """A product entity"""
    id: str: Field(description="Unique product identifier")
    name: str: Field(description="Product name")
    price: float: Field(description="Product price", ge=0.0, le=1000000.0)
    category: str: Field(description="Product category", enum=['electronics', 'clothing', 'books', 'other'])

class RootModel(BaseModel):
    """Root model that can represent any entity type."""
    type: str = Field(description='The type of entity')
    data: Union[Person, Product] = Field(description='The entity data')

# Example usage:
# from .models import Person, Product
#
# # Create an instance
# instance = Person(...)
#
# # Validate data
# validated = Person.model_validate(data_dict)