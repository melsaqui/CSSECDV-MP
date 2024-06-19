import os
import time
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import re
from werkzeug.utils import secure_filename
import sys


app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Lacsapcshs2020*'
app.config['MYSQL_DB'] = 'cssecdv-mp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Initialize MySQL
mysql = MySQL(app)
# Configure upload folder and allowed file types
UPLOAD_FOLDER = './upload_folder'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Dictionary to track login attempts per IP address
login_attempts = {}

# Constants for brute force protection
MAX_ATTEMPTS = 5
BLOCK_DURATION = 300  # 5 minutes
TIME_FRAME = 600  # 10 minutes

# Function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to limit login attempts per IP address
def limit_attempts():
    client_ip = request.remote_addr
    current_time = time.time()

    if client_ip in login_attempts:
        attempts, first_attempt_time = login_attempts[client_ip]

        if attempts >= MAX_ATTEMPTS:
            if current_time - first_attempt_time < BLOCK_DURATION:
                return False
            else:
                # Reset attempts after block duration
                login_attempts[client_ip] = [0, current_time]
        elif current_time - first_attempt_time > TIME_FRAME:
            # Reset attempts after the time frame
            login_attempts[client_ip] = [0, current_time]
    else:
        login_attempts[client_ip] = [0, current_time]

    return True

# Route to handle profile picture upload
@app.route('/upload-profile-picture', methods=['GET','POST'])
def upload_profile_pic():
    if 'loggedin' not in session:
        return redirect('/login')
    
    
    
    if request.method == 'POST':
        if 'profile_pic' not in request.files:
            flash('No file part')
            return redirect('/')
    
        file = request.files['profile_pic']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

        # Update database with profile picture path or filename
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE accounts SET profile_pic = %s WHERE id = %s', (filename, session['id']))
            mysql.connection.commit()
            cursor.close()

            flash('Profile picture uploaded successfully')
            return redirect('/')

        else:
            flash('Invalid file format. Allowed formats are .jpg, .jpeg, .png')
            return redirect(request.url)

# Route to handle login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session and session['loggedin']:
        return redirect('/')
    else:
        msg = ''
        if request.method == 'POST' and 'pass' in request.form and 'user' in request.form:
            if not limit_attempts():
                msg = 'Too many login attempts. Please try again later.'
                return render_template('login.html', msg=msg)

            password = request.form['pass']
            user = request.form['user']

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE email = %s', (user,))
            account = cursor.fetchone()

            if account and bcrypt.checkpw(password.encode('utf-8'), account['password']):
                session['loggedin'] = True
                session['id'] = account['id']
                session['email'] = account['email']
                msg = 'Logged in successfully!'
                return redirect('/')
            else:
                msg = 'Incorrect username / password!'
                # Increment failed attempts for the current IP
                client_ip = request.remote_addr
                if client_ip in login_attempts:
                    login_attempts[client_ip][0] += 1
                else:
                    login_attempts[client_ip] = [1, time.time()]

        return render_template('login.html', msg=msg)
    #else:
    #    return redirect('/')

# Additional routes and functions as per your existing application...

@app.route('/admin')
def admin():
    if session and session['loggedin']:

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (session['id'], ))
        account = cursor.fetchone()
        if account['admin'] == 1:  
            return render_template('admin.html')
        else: 
            return redirect('/')
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)
    session.clear()
    return redirect('/login')

@app.route('/')
def home():
    if session and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE email = %s and id = %s', (session['email'], session['id'],))
        account = cursor.fetchone()
        user = account['fname']  
        return render_template('index.html', user=user, admin=account['admin'])
    else:
        return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session and session['loggedin']:
       return redirect('/')
    else:
        msg = ''
        if request.method == 'POST' and 'psw-repeat' in request.form and 'psw' in request.form and 'email' in request.form and 'fname' in request.form and 'lname' in request.form and 'phone' in request.form:
            fname = request.form['fname']
            lname = request.form['lname']
            password = request.form['psw']
            reppass = request.form['psw-repeat']
            email = request.form['email']
            phone = request.form['phone']
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(bytes(password, 'utf-8'), salt)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE email = %s', (email,))
            account = cursor.fetchone()
            if account:
                msg = 'Account already exists!'
            elif not re.match(r'^(([a-zA-Z0-9]+)(([-_.][a-zA-Z0-9]+)*))@(([a-zA-Z0-9-]+\.[a-zA-Z]{2,})+)$', email):
                msg = 'Invalid email address!'
            elif not re.match(r'[A-Za-z]+', fname):
                msg = 'Invalid Name!'
            elif not re.match(r'[A-Za-z]+', lname):
                msg = 'Invalid Name!'
            elif not re.match(r'^09\d{9}$', phone) and not re.match(r'^[+]{1}(?:[0-9\-\(\)\/\.]\s?){6,15}[0-9]{1}$', phone):
                msg = "Invalid phone number"
            elif password != reppass:
                msg = "Passwords not matching"
            elif not email or not password or not phone or not reppass or not fname or not lname:
                msg = 'Please fill out the form!'
            else:
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s, %s, False,NULL)', (fname, lname, email, phone, hashed))
                mysql.connection.commit()
                msg = 'You have successfully registered!'

        elif request.method == 'POST':
            msg = 'Please fill out the form!'

        return render_template('reg.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)
