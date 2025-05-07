import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import *

DATABASE_URL = "sqlite:///example.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()

    users = [
        User(name="amir", age=30, email="alice@example.com"),
        User(name="ali", age=25, email="bob@example.com"),
        User(name="mohammad", age=35, email="charlie@example.com"),
    ]
    session.add_all(users)
    session.commit()

    foods = [
        Food(name="spaghetti", price=12.5, description="Classic Italian pasta with rich tomato sauce."),
        Food(name="salad", price=15.0, description="Fresh garden vegetables with a light vinaigrette."),
        Food(name="sandwich", price=14.0, description="Grilled chicken sandwich with lettuce and mayo."),
    ]

    session.add_all(foods)
    session.commit()

    orders = [
        Order(food_id=1, user_id=1),
        Order(food_id=2, user_id=1),
        Order(food_id=3, user_id=2),
    ]
    session.add_all(orders)
    session.commit()

    session.close()
    print("The database was successfully expanded and populated with sample data.")


if __name__ == "__main__":
    if not os.path.exists("example.db"):
        init_db()
    else:
        print("The database 'example.db' already exists.")
