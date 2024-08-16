from flask import Blueprint, render_template, request, redirect, url_for, flash,current_app
from flask_login import login_user, logout_user, current_user, login_required
from . import db
from .forms import CategoryForm, ProductForm, UserManagementForm
from .models import Category, Product, User, db,Payment,Cart, Order, OrderItem
from werkzeug.security import generate_password_hash
import os
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)
admin = Blueprint('admin', __name__, url_prefix='/admin')

@main.route('/')
@main.route('/home/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)

@main.route('/search')
def search():
    query = request.args.get('q')
    products = []
    if query:
        products = Product.query.filter(Product.name.contains(query)).all()
        if not products:
            products = Product.query.filter(Product.description.contains(query)).all()
    return render_template('home.html', products=products)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Login successful.', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')

    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password, role='buyer')
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@main.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', cart_items=cart_items)

@main.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    # Get the product details
    product = Product.query.get_or_404(product_id)
    
    # Check if the item is already in the cart
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()

    if cart_item:
        # Update quantity if item already exists in the cart
        cart_item.quantity += 1
    else:
        # Add new item to the cart
        cart_item = Cart(
            user_id=current_user.id,
            product_id=product.id,
            quantity=1
        )
        db.session.add(cart_item)

    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect(url_for('main.home'))

@main.route('/update_cart/<int:cart_id>/<action>')
@login_required
def update_cart(cart_id, action):
    cart_item = Cart.query.get_or_404(cart_id)
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('main.cart'))

@main.route('/remove_from_cart/<int:cart_id>')
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('main.cart'))


@main.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('main.home'))

    # Calculate total price
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Create a new order
    new_order = Order(
        user_id=current_user.id,
        total_price=total_price
    )
    db.session.add(new_order)
    db.session.commit()  # Commit to get the order_id

    # Add order items
    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_item)
    
    db.session.commit()  # Commit to save all order items

    # Clear cart
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash('Order placed successfully!', 'success')
    return redirect(url_for('main.home'))


@main.route('/buy_now/<int:product_id>', methods=['POST'])
@login_required
def buy_now(product_id):
    # Your existing logic for handling the buy now action
    product = Product.query.get_or_404(product_id)
    
    # Create a new order
    new_order = Order(
        user_id=current_user.id,
        total_price=product.price,  # Adjust as needed for multiple items
    )
    db.session.add(new_order)
    db.session.commit()  # Commit to get the order_id

    # Add an order item for the product
    order_item = OrderItem(
        order_id=new_order.id,
        product_id=product.id,
        quantity=1,  # Adjust quantity as needed
        price=product.price
    )
    db.session.add(order_item)
    db.session.commit()  # Commit to save the order item

    flash('Order placed successfully!', 'success')
    return redirect(url_for('main.home'))



# Admin Routes
def admin_only():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

# Manage Users
@admin.route('/manage_users')
@login_required
def manage_users():
    admin_only()
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

# Manage Products

@admin.route('/manage_products', methods=['GET', 'POST'])
@login_required

def manage_products():
    admin_only()
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    form = ProductForm()
    if form.validate_on_submit():
        if form.image.data:
            # Get the upload folder path from the app config
            uploads_dir = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)

            image_file = secure_filename(form.image.data.filename)
            image_path = os.path.join(uploads_dir, image_file)
            form.image.data.save(image_path)
        else:
            image_file = 'default.jpg'

        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            category_id=form.category.data,
            image_file=image_file
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.manage_products'))
    
    products = Product.query.all()
    return render_template('admin/manage_products.html', products=products, form=form)

# Manage Categories
@admin.route('/manage_categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    admin_only()
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
        return redirect(url_for('admin.manage_categories'))
    
    categories = Category.query.all()
    return render_template('admin/manage_categories.html', form=form, categories=categories)

# View Payments
@admin.route('/view_payments')
@login_required
def view_payments():
    admin_only()
    payments = Payment.query.all()
    return render_template('admin/view_payments.html', payments=payments)

# View Reports
@admin.route('/view_reports')
@login_required
def view_reports():
    admin_only()
    # Example report data
    return render_template('admin/view_reports.html')

# User Management (Edit/Delete users)
@admin.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    admin_only()
    user = User.query.get_or_404(user_id)
    form = UserManagementForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
    return render_template('admin/edit_user.html', form=form, user=user)

@admin.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    admin_only()
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin.manage_users'))