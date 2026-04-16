#!/usr/bin/env python3
"""
Database Seeder for Food Delivery App

This script populates the database with sample data for development and testing.
Run this after creating the database tables with db.create_all().

Usage:
    python seed.py

Requirements:
    - Flask app context
    - Database tables created
"""

from app import app, db, User, Restaurant, MenuItem, Order, OrderItem
from werkzeug.security import generate_password_hash
import random
from datetime import datetime

def create_sample_users():
    """Create sample users with different roles."""
    users_data = [
        {
            'username': 'customer1',
            'email': 'customer1@example.com',
            'password': 'password123',
            'role': 'customer'
        },
        {
            'username': 'customer2',
            'email': 'customer2@example.com',
            'password': 'password123',
            'role': 'customer'
        },
        {
            'username': 'restaurant_owner1',
            'email': 'owner1@example.com',
            'password': 'password123',
            'role': 'restaurant_owner'
        },
        {
            'username': 'restaurant_owner2',
            'email': 'owner2@example.com',
            'password': 'password123',
            'role': 'restaurant_owner'
        },
        {
            'username': 'delivery1',
            'email': 'delivery1@example.com',
            'password': 'password123',
            'role': 'delivery_person'
        }
    ]

    users = []
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            password=generate_password_hash(user_data['password']),
            role=user_data['role']
        )
        users.append(user)
        db.session.add(user)

    db.session.commit()
    print(f"Created {len(users)} sample users")
    return users

def create_sample_restaurants(users):
    """Create sample restaurants owned by restaurant owners."""
    restaurant_owners = [u for u in users if u.role == 'restaurant_owner']

    restaurants_data = [
        {
            'name': 'Italian Corner',
            'address': '123 Main St, Cityville',
            'owner': restaurant_owners[0]
        },
        {
            'name': 'Burger House',
            'address': '456 Oak Ave, Townburg',
            'owner': restaurant_owners[1]
        },
        {
            'name': 'Pasta Palace',
            'address': '789 Pine Rd, Villagetown',
            'owner': restaurant_owners[0]
        }
    ]

    restaurants = []
    for rest_data in restaurants_data:
        restaurant = Restaurant(
            name=rest_data['name'],
            address=rest_data['address'],
            owner_id=rest_data['owner'].id
        )
        restaurants.append(restaurant)
        db.session.add(restaurant)

    db.session.commit()
    print(f"Created {len(restaurants)} sample restaurants")
    return restaurants

def create_sample_menu_items(restaurants):
    """Create sample menu items for each restaurant."""
    menu_items_data = [
        # Italian Corner items
        [
            {'name': 'Margherita Pizza', 'description': 'Classic tomato, mozzarella, basil', 'price': 12.99},
            {'name': 'Pepperoni Pizza', 'description': 'Pepperoni, cheese, tomato sauce', 'price': 14.99},
            {'name': 'Pasta Carbonara', 'description': 'Creamy pasta with bacon and parmesan', 'price': 13.50},
            {'name': 'Caesar Salad', 'description': 'Romaine lettuce, croutons, parmesan', 'price': 8.99}
        ],
        # Burger House items
        [
            {'name': 'Classic Burger', 'description': 'Beef patty, lettuce, tomato, cheese', 'price': 10.99},
            {'name': 'Bacon Burger', 'description': 'Beef patty with crispy bacon', 'price': 12.99},
            {'name': 'Chicken Burger', 'description': 'Grilled chicken breast burger', 'price': 11.50},
            {'name': 'French Fries', 'description': 'Crispy golden fries', 'price': 4.99}
        ],
        # Pasta Palace items
        [
            {'name': 'Spaghetti Bolognese', 'description': 'Spaghetti with meat sauce', 'price': 11.99},
            {'name': 'Fettuccine Alfredo', 'description': 'Creamy fettuccine pasta', 'price': 12.99},
            {'name': 'Lasagna', 'description': 'Layered pasta with meat and cheese', 'price': 15.99},
            {'name': 'Garlic Bread', 'description': 'Toasted bread with garlic butter', 'price': 5.99}
        ]
    ]

    all_menu_items = []
    for i, restaurant in enumerate(restaurants):
        for item_data in menu_items_data[i]:
            menu_item = MenuItem(
                name=item_data['name'],
                description=item_data['description'],
                price=item_data['price'],
                restaurant_id=restaurant.id
            )
            all_menu_items.append(menu_item)
            db.session.add(menu_item)

    db.session.commit()
    print(f"Created {len(all_menu_items)} sample menu items")
    return all_menu_items

def create_sample_orders(users, restaurants, menu_items):
    """Create sample orders with order items."""
    customers = [u for u in users if u.role == 'customer']

    order_statuses = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered']

    orders_data = [
        {
            'customer': customers[0],
            'restaurant': restaurants[0],
            'status': 'delivered',
            'delivery_address': '123 Customer St, Cityville',
            'items': [
                {'menu_item': menu_items[0], 'quantity': 1},  # Margherita Pizza
                {'menu_item': menu_items[3], 'quantity': 1}   # Caesar Salad
            ]
        },
        {
            'customer': customers[1],
            'restaurant': restaurants[1],
            'status': 'preparing',
            'delivery_address': '456 Buyer Ave, Townburg',
            'items': [
                {'menu_item': menu_items[4], 'quantity': 2},  # Classic Burger
                {'menu_item': menu_items[7], 'quantity': 1}   # French Fries
            ]
        },
        {
            'customer': customers[0],
            'restaurant': restaurants[2],
            'status': 'confirmed',
            'delivery_address': '123 Customer St, Cityville',
            'items': [
                {'menu_item': menu_items[8], 'quantity': 1},  # Spaghetti Bolognese
                {'menu_item': menu_items[11], 'quantity': 2}  # Garlic Bread
            ]
        }
    ]

    orders = []
    for order_data in orders_data:
        # Calculate total amount
        total_amount = sum(item['menu_item'].price * item['quantity'] for item in order_data['items'])

        order = Order(
            customer_id=order_data['customer'].id,
            restaurant_id=order_data['restaurant'].id,
            status=order_data['status'],
            total_amount=total_amount,
            delivery_address=order_data['delivery_address']
        )
        orders.append(order)
        db.session.add(order)
        db.session.flush()  # Get order.id

        # Create order items
        for item_data in order_data['items']:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item_data['menu_item'].id,
                quantity=item_data['quantity']
            )
            db.session.add(order_item)

    db.session.commit()
    print(f"Created {len(orders)} sample orders with their items")
    return orders

def main():
    """Main function to seed the database."""
    print("Starting database seeding...")

    with app.app_context():
        # Clear existing data (optional, uncomment if needed)
        # db.drop_all()
        # db.create_all()

        try:
            users = create_sample_users()
            restaurants = create_sample_restaurants(users)
            menu_items = create_sample_menu_items(restaurants)
            orders = create_sample_orders(users, restaurants, menu_items)

            print("\nDatabase seeding completed successfully!")
            print(f"Total users: {len(users)}")
            print(f"Total restaurants: {len(restaurants)}")
            print(f"Total menu items: {len(menu_items)}")
            print(f"Total orders: {len(orders)}")

        except Exception as e:
            print(f"Error during seeding: {e}")
            db.session.rollback()

if __name__ == '__main__':
    main()