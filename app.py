from flask import Flask, render_template, session, redirect, url_for, request
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, Email, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'AZsx@1209'
app.config['MYSQL_DB'] = 'amazon'

mysql = MySQL(app)

app.secret_key = 'abc@123'


def is_password_strong(password):
    if len(password) < 8:
        return False
    if not re.search(r"[a-z]", password) or not re.search(r"[A-Z]", password) or not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*()-+{}|\"<>]?", password):
        return False
    return True


def is_logged_in():
    return 'email' in session


class User:
    def __init__(self, user_id, username, email, password):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password


class signin_form(FlaskForm):
    username = StringField('Your Name', validators=[InputRequired()])
    email = StringField('Your Mail', validators=[InputRequired(), Email(message='Invalid email')])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=15)])
    confirm_password = PasswordField('Confirm Password', validators=[InputRequired(), EqualTo('password', message='Password must match')])
    submit = SubmitField('Sign Up')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = signin_form()
    if form.validate_on_submit():
        name = form.username.data
        email = form.email.data
        password = form.confirm_password.data
        if not is_password_strong(password):
            return redirect(url_for('signup'))
        hashed_password = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute('select id from signup where email = %s', (email,))
        old_user = cur.fetchone()
        if old_user:
            cur.close()
            return render_template('signup.html')
        cur.execute('INSERT INTO signup (name, email, password) VALUES (%s, %s, %s)', (name, email, hashed_password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)


class login_form(FlaskForm):
    email = StringField('Your Mail', validators=[InputRequired(), Email(message='Invalid email')])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=15)])
    submit = SubmitField('sign in')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = login_form()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        cur = mysql.connection.cursor()
        cur.execute('SELECT id, name, email, password FROM signup WHERE email = %s', (email,))
        login_id = cur.fetchone()
        cur.close()
        if login_id and check_password_hash(login_id[3], password):
            user = User(user_id=login_id[0], username=login_id[1], email=login_id[2], password=login_id[3])
            session['email'] = user.email
            session['username'] = user.username
            return redirect(url_for('home'))
    return render_template('login.html', form=form)


@app.route('/')
def home():
    if is_logged_in():
        email = session['email']
        cur = mysql.connection.cursor()
        cur.execute('SELECT SUM(quantity) FROM cart WHERE email = %s', (email,))
        cart_count = cur.fetchone()[0] or 0

        cur.execute('SELECT name FROM signup WHERE email = %s', (email,))
        user = cur.fetchone()
        user_name = user[0] if user else None

        cur.close()
    else:
        cart_count = 0
        user_name = None

    return render_template('navbar.html', cart_count=cart_count, user_name=user_name)


@app.route('/cart')
def cart_pre_login():
    cart_count = 0
    if is_logged_in():
        email = session['email']
        cur = mysql.connection.cursor()
        cur.execute('SELECT SUM(quantity) FROM cart WHERE email = %s', (email,))
        cart_count = cur.fetchone()[0] or 0
        cur.close()
    return render_template('cart_pre_login.html', cart_count=cart_count)


@app.route('/mobile')
def mobile():
    if is_logged_in():
        email = session['email']
        cur = mysql.connection.cursor()
        cur.execute('SELECT SUM(quantity) FROM cart WHERE email = %s', (email,))
        cart_count = cur.fetchone()[0] or 0

        cur.execute('SELECT name FROM signup WHERE email = %s', (email,))
        user_name = cur.fetchone()[0]
        cur.close()
    else:
        cart_count = 0
        user_name = None

    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM most_gifted')
    mostgifted = cur.fetchall()

    cur.execute('SELECT * FROM featured')
    featured = cur.fetchall()

    cur.execute('SELECT * FROM best_seller')
    bestseller = cur.fetchall()

    cur.execute('SELECT * FROM recommended')
    recommended = cur.fetchall()

    cur.execute('SELECT * FROM new_release')
    newrelease = cur.fetchall()

    cur.execute('SELECT * FROM top_rated')
    toprated = cur.fetchall()

    cur.close()
    return render_template('mobile.html', data1=mostgifted, data2=featured, data3=bestseller, data4=recommended,
                           data5=newrelease, data6=toprated, cart_count=cart_count, user_name=user_name)


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if not is_logged_in():
        return redirect(url_for('login'))

    email = session['email']
    image_url = request.form['image_url']
    mrp = float(request.form['mrp'].replace(',', ''))
    selling_price = float(request.form['selling_price'].replace(',', ''))
    model_name = request.form['model_name']
    storage_details = request.form['storage_details']
    color = request.form['color']
    star_rating = float(request.form['star_rating'])

    num_reviews = int(request.form['num_reviews'].replace(',', ''))
    quantity = int(request.form.get('quantity', 1))

    total_price = selling_price * quantity

    cur = mysql.connection.cursor()
    cur.execute("""
            INSERT INTO cart (email, image_url, mrp, selling_price, model_name, storage_details, color, star_rating, num_reviews, quantity, total_price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
    email, image_url, mrp, selling_price, model_name, storage_details, color, star_rating, num_reviews, quantity,
    total_price))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('cart_post_login'))


@app.route('/quantity/<int:id>', methods=['POST'])
def update_quantity(id):
    if not is_logged_in():
        return redirect(url_for('login'))

    action = request.form.get('action')
    quantity = int(request.form.get('quantity'))

    if action == 'decrease' and quantity > 1:
        quantity -= 1
    elif action == 'increase':
        quantity += 1

    cur = mysql.connection.cursor()
    cur.execute('UPDATE cart SET quantity = %s, total_price = quantity * selling_price WHERE id = %s', (quantity, id))
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('cart_post_login'))


@app.route('/cartitems')
def cart_post_login():
    if is_logged_in():
        email = session['email']
        cur = mysql.connection.cursor()

        cur.execute('SELECT SUM(quantity) FROM cart WHERE email = %s', (email,))
        cart_count = cur.fetchone()[0] or 0

        cur.execute('SELECT * FROM cart WHERE email = %s', (email,))
        cart_items = cur.fetchall()

        subtotal = sum(item[11] for item in cart_items)

        cur.execute('SELECT name FROM signup WHERE email = %s', (email,))
        user_name = cur.fetchone()[0]

        cur.close()
        return render_template('cart_post_login.html', cart_items=cart_items, cart_count=cart_count,
                               user_name=user_name, subtotal=subtotal)
    else:
        return redirect(url_for('login'))


@app.route('/delete/<int:id>', methods=['POST', 'GET'])
def delete(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE from cart where id = %s', (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('cart_post_login'))


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
