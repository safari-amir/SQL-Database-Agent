import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Base, User, Food, Order

# SQLite database URL
DATABASE_URL = "sqlite:///test.db"

# SQLAlchemy engine and session configuration
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Function to initialize and populate the database
def setup_database():
    # Create all tables defined by Base subclasses
    Base.metadata.create_all(bind=engine)

    # Create a new session
    session = SessionLocal()

    # Sample user data
    users = [
        User(name="Amir", email="amir@example.com", password="password123"),
        User(name="Sara", email="sara@example.com", password="password1234"),
        User(name="Ali", email="ali@example.com", password="password12345"),
        User(name="Zahra", email="Zahra@example.com", password="password123456"),
        User(name="Reza", email="reza@example.com", password="password1234567")
    ]

    # Sample food data
    foods = [
        Food(name="Pizza", price=10),
        Food(name="Burger", price=5),
        Food(name="Pasta", price=8),
        Food(name="Salad", price=4),
        Food(name="Sushi", price=12)
    ]

    # Sample orders
    orders = [
        Order(user_id=1, food_id=1),
        Order(user_id=2, food_id=2),
        Order(user_id=3, food_id=3),
        Order(user_id=4, food_id=4),
        Order(user_id=5, food_id=5)
    ]

    # Add all data to the session and commit to the database
    session.add_all(users)
    session.add_all(foods)
    session.add_all(orders)
    session.commit()

    # Close the session
    session.close()
    print("Database setup complete.")


# Run the setup only if the database file doesn't already exist
if __name__ == "__main__":
    if not os.path.exists("test.db"):
        setup_database()
    else:
        print("Database already exists.")
