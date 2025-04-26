from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


# Base class for declarative class definitions
Base = declarative_base()

# User model/table definition
class User(Base):
    __tablename__ = 'users'  # Table name in the database
    id = Column(Integer, primary_key=True)  # Primary key
    name = Column(String)
    email = Column(String, unique=True)  # Unique constraint on email
    password = Column(String, unique=True)  # Typo fixed: 'uniqwue' to 'unique'

    # Relationship with the Order table
    orders = relationship("Order", back_populates="user")


# Food model/table definition
class Food(Base):
    __tablename__ = 'foods'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)

    # Relationship with the Order table
    orders = relationship("Order", back_populates="food")


# Order model/table definition
class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # Foreign key to users table
    food_id = Column(Integer, ForeignKey('foods.id'))  # Foreign key to foods table

    # Relationships to User and Food
    user = relationship("User", back_populates="orders")
    food = relationship("Food", back_populates="orders")
