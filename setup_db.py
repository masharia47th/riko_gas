from app import create_app, db
from app.models import User, Product, Category, Order, OrderItem, Cart, Payment

# Create the Flask application context
app = create_app()

with app.app_context():
    # Create all the database tables
    db.create_all()

    # Populate initial data for categories
    categories = ['Gas_Cylinders', 'Gas_    Appliances']
    for name in categories:
        category = Category(name=name)
        db.session.add(category)

    # Create an admin user
    admin = User(username='admin', email='admin@example.com', role='admin')
    admin.set_password('adminpassword')  # Set a secure password for the admin

    # Create a buyer user
    buyer = User(username='buyer', email='buyer@example.com', role='buyer')
    buyer.set_password('buyerpassword')  # Set a secure password for the buyer

    # Add the users to the session
    db.session.add(admin)
    db.session.add(buyer)

    # Commit the changes to the database
    db.session.commit()

    print("Database created and populated successfully with admin and buyer users.")
