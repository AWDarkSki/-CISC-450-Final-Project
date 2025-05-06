from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Secret key for session (make sure to change it in production)
app.secret_key = 'your-secret-key'

class User(UserMixin):
    def __init__(self, user_id, email, role):
        self.id = user_id
        self.email = email
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('convention_clothing_catalogue.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, email, role FROM Users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        conn = sqlite3.connect('convention_clothing_catalogue.db')
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Users (email, password_hash, first_name, last_name, role)
                VALUES (?, ?, ?, ?, 'user')
            """, (email, password, first_name, last_name))
            conn.commit()
        except sqlite3.IntegrityError:
            return "User with that email already exists"
        finally:
            conn.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('convention_clothing_catalogue.db')
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, password_hash, role FROM Users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            user_obj = User(user_id=user[0], email=email, role=user[2])
            login_user(user_obj)
            return redirect(url_for('index'))

        return "Invalid email or password"

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    category = request.args.get('category', 'all')
    size = request.args.get('size', 'all')
    search = request.args.get('search', '').lower()
    convention = request.args.get('convention', 'all')

    query = """
        SELECT p.*
        FROM Products p
        LEFT JOIN Product_Convention pc ON p.product_id = pc.product_id
        LEFT JOIN Conventions c ON pc.convention_id = c.convention_id
        WHERE 1=1
    """
    params = []

    if category != 'all':
        query += " AND p.category = ?"
        params.append(category)

    if size != 'all':
        query += " AND p.size = ?"
        params.append(size)

    if search:
        query += " AND (p.name LIKE ? OR p.description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if convention != 'all':
        query += " AND c.name = ?"
        params.append(convention)

    query += " GROUP BY p.product_id"

    try:
        conn = sqlite3.connect('convention_clothing_catalogue.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        products = cursor.fetchall()
        conn.close()

        return jsonify([dict(product) for product in products])
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500


@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    user_id = current_user.id
    conn = sqlite3.connect('convention_clothing_catalogue.db')
    cursor = conn.cursor()

    # Check if already in wishlist
    cursor.execute("SELECT 1 FROM Wishlists WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    exists = cursor.fetchone()

    if exists:
        conn.close()
        # Redirect back with a message or silently ignore
        return redirect(url_for('view_wishlist'))  # or back to product page

    # Add to wishlist if not already present
    cursor.execute("INSERT INTO Wishlists (user_id, product_id) VALUES (?, ?)", (user_id, product_id))
    conn.commit()
    conn.close()

    return redirect(url_for('view_wishlist'))



@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if current_user.role != 'admin':
        return "Access denied", 403

    conn = sqlite3.connect('convention_clothing_catalogue.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        description = request.form.get('description')
        size = request.form['size']
        category = request.form['category']
        image_url = request.form.get('image_url')
        stock_quantity = request.form['stock_quantity']
        convention_ids = request.form.get('convention_ids', '')

        cursor.execute("""
            INSERT INTO Products (name, price, description, size, category, image_url, stock_quantity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, price, description, size, category, image_url, stock_quantity))
        product_id = cursor.lastrowid

        # Link conventions if provided
        for cid in [c.strip() for c in convention_ids.split(',') if c.strip().isdigit()]:
            cursor.execute("INSERT INTO Product_Convention (product_id, convention_id) VALUES (?, ?)", (product_id, int(cid)))

        conn.commit()

    # Fetch all products and their conventions
    cursor.execute("""
        SELECT p.*, GROUP_CONCAT(c.name) as convention_names
        FROM Products p
        LEFT JOIN Product_Convention pc ON p.product_id = pc.product_id
        LEFT JOIN Conventions c ON pc.convention_id = c.convention_id
        GROUP BY p.product_id
    """)
    products = cursor.fetchall()

    product_list = []
    for row in products:
        product_dict = dict(row)
        product_dict['conventions'] = row['convention_names'].split(',') if row['convention_names'] else []
        product_list.append(product_dict)

    conn.close()
    return render_template('admin_products.html', products=product_list)

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':
        return "Access denied", 403

    conn = sqlite3.connect('convention_clothing_catalogue.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Products WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_products'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    try:
        conn = sqlite3.connect('convention_clothing_catalogue.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()

        if product:
            return jsonify(dict(product))
        else:
            return jsonify({"error": "Product not found"}), 404
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

# In app.py
@app.route('/create_admin')
def create_admin():
    from werkzeug.security import generate_password_hash
    password = generate_password_hash('adminpass')

    conn = sqlite3.connect('convention_clothing_catalogue.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Users (email, password_hash, first_name, last_name, role)
        VALUES (?, ?, ?, ?, ?)
    ''', ('admin2@example.com', password, 'Admin', 'User', 'admin'))
    conn.commit()
    conn.close()

    return "Admin user created. Email: admin2@example.com, Password: adminpass"

@app.route('/product/<int:product_id>/conventions')
def get_product_conventions(product_id):
    conn = sqlite3.connect('convention_clothing_catalogue.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.name
        FROM Conventions c
        JOIN Product_Convention pc ON c.convention_id = pc.convention_id
        WHERE pc.product_id = ?
    """, (product_id,))
    conventions = [row['name'] for row in cursor.fetchall()]
    conn.close()

    return jsonify(conventions)


@app.route('/wishlist')
@login_required
def view_wishlist():
    user_id = current_user.id
    conn = sqlite3.connect('convention_clothing_catalogue.db')
    conn.row_factory = sqlite3.Row  # Enable dict-like row access
    cursor = conn.cursor()

    cursor.execute('''
        SELECT Products.product_id, Products.name, Products.description, Products.price, 
               Products.image_url, Products.size, Products.category
        FROM Products
        INNER JOIN Wishlists ON Products.product_id = Wishlists.product_id
        WHERE Wishlists.user_id = ?
    ''', (user_id,))

    wishlist_items = cursor.fetchall()
    conn.close()

    return render_template('wishlist.html', wishlist_items=wishlist_items)


@app.route('/wishlist/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_from_wishlist(product_id):
    user_id = current_user.id
    conn = sqlite3.connect('convention_clothing_catalogue.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Wishlists WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    conn.commit()
    conn.close()

    return redirect(url_for('view_wishlist'))

@app.route('/conventions')
def get_conventions():
    conn = sqlite3.connect('convention_clothing_catalogue.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT name FROM Conventions ORDER BY name")
    conventions = [row['name'] for row in cursor.fetchall()]
    conn.close()

    return jsonify(conventions)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    conn = sqlite3.connect('convention_clothing_catalogue.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])

        cursor.execute('''
            UPDATE products SET name = ?, description = ?, price = ?
            WHERE product_id = ?
        ''', (name, description, price, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_products'))

    # GET: load product data
    cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        return 'Product not found', 404

    product_dict = {
        'product_id': product[0],
        'name': product[1],
        'description': product[2],
        'price': product[3]
    }

    return render_template('edit_product.html', product=product_dict)


# Run the app
if __name__ == '__main__':
    app.run(debug=True)