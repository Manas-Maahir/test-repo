from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///food_delivery.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='customer')  # customer, restaurant_owner, delivery_person

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, preparing, out_for_delivery, delivered
    total_amount = db.Column(db.Float, nullable=False)
    delivery_address = db.Column(db.String(300), nullable=False)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    restaurants = Restaurant.query.all()
    return render_template('home.html', restaurants=restaurants)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form.get('role', 'customer')
        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/restaurant/<int:restaurant_id>')
@login_required
def restaurant_menu(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return render_template('restaurant.html', restaurant=restaurant, menu_items=menu_items)

@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
@login_required
def add_to_cart(item_id):
    if 'cart' not in session:
        session['cart'] = {}
    quantity = int(request.form['quantity'])
    session['cart'][str(item_id)] = session['cart'].get(str(item_id), 0) + quantity
    session.modified = True
    flash('Item added to cart!')
    return redirect(request.referrer)

@app.route('/cart')
@login_required
def cart():
    cart_items = []
    total = 0
    if 'cart' in session:
        for item_id, qty in session['cart'].items():
            item = MenuItem.query.get(int(item_id))
            if item:
                cart_items.append({'item': item, 'quantity': qty, 'subtotal': item.price * qty})
                total += item.price * qty
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    if 'cart' not in session or not session['cart']:
        flash('Cart is empty!')
        return redirect(url_for('cart'))
    
    delivery_address = request.form['delivery_address']
    total = 0
    order_items = []
    restaurant_id = None
    for item_id, qty in session['cart'].items():
        item = MenuItem.query.get(int(item_id))
        if item:
            order_items.append({'item_id': item.id, 'quantity': qty})
            total += item.price * qty
            if restaurant_id is None:
                restaurant_id = item.restaurant_id
            elif restaurant_id != item.restaurant_id:
                flash('Cannot order from multiple restaurants at once!')
                return redirect(url_for('cart'))
    
    order = Order(customer_id=current_user.id, restaurant_id=restaurant_id, total_amount=total, delivery_address=delivery_address)
    db.session.add(order)
    db.session.commit()
    
    for oi in order_items:
        order_item = OrderItem(order_id=order.id, menu_item_id=oi['item_id'], quantity=oi['quantity'])
        db.session.add(order_item)
    db.session.commit()
    
    session.pop('cart', None)
    flash('Order placed successfully!')
    return redirect(url_for('orders'))

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(customer_id=current_user.id).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        flash('Access denied!')
        return redirect(url_for('home'))
    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template('order_details.html', order=order, order_items=order_items)

# Admin routes for restaurant owners
@app.route('/add_restaurant', methods=['GET', 'POST'])
@login_required
def add_restaurant():
    if current_user.role != 'restaurant_owner':
        flash('Access denied!')
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        restaurant = Restaurant(name=name, address=address, owner_id=current_user.id)
        db.session.add(restaurant)
        db.session.commit()
        flash('Restaurant added!')
        return redirect(url_for('home'))
    return render_template('add_restaurant.html')

@app.route('/add_menu_item/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def add_menu_item(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    if restaurant.owner_id != current_user.id:
        flash('Access denied!')
        return redirect(url_for('home'))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        item = MenuItem(name=name, description=description, price=price, restaurant_id=restaurant_id)
        db.session.add(item)
        db.session.commit()
        flash('Menu item added!')
        return redirect(url_for('restaurant_menu', restaurant_id=restaurant_id))
    return render_template('add_menu_item.html', restaurant=restaurant)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)