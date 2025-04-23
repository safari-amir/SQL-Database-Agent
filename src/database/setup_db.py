import os 
form sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String, uniqwue=True)

    orders = relationship("Order", back_populates="user")


class Food(Base):
    __tablename__ = 'foods'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    price = Column(Integer)

    orders = relationship("Order", back_populates="food")


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    food_id = Column(Integer, ForeignKey('foods.id'))

    user = relationship("User", back_populates="orders")
    food = relationship("Food", back_populates="orders")


DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_database():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    users = [
        User(name="Amir", email="amir@example.com", password="password123"),
        User(name="Sara", email="sara@example.com", password="password1234"),
        User(name="Ali", email="ali@example.com", password="password12345"),
        User(name="Zahra", email="Zahra@example.com", password="password123456"),
        User(name="Reza", email="reza@example.com", password="password1234567")
    ]
    foods = [
        Food(name="Pizza", price=10),
        Food(name="Burger", price=5),
        Food(name="Pasta", price=8),
        Food(name="Salad", price=4),
        Food(name="Sushi", price=12)
    ]
    orders = [
        Order(user_id=1, food_id=1),
        Order(user_id=2, food_id=2),
        Order(user_id=3, food_id=3),
        Order(user_id=4, food_id=4),
        Order(user_id=5, food_id=5)
    ]
    session.add_all(users)
    session.add_all(foods)  
    session.add_all(orders)
    session.commit()

    session.close()
    print("Database setup complete.")

if __name__ == "__main__":
    if not os.path.exists("test.db"):
        setup_database()
    else:
        print("Database already exists.")