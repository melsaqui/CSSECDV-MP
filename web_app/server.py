import os
import time
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import re
from werkzeug.utils import secure_filename
import sys
from datetime import timedelta
from dotenv import load_dotenv #pip install python-dotenv


app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'
'''
# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Lacsapcshs2020*'
app.config['MYSQL_DB'] = 'cssecdv-mp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
'''
# MAKE YOUR OWN .env file based on your SQL configurations
load_dotenv()

app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST")
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB")
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

app.permanent_session_lifetime = timedelta(minutes=30)

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
    if session and 'loggedin' in session.keys() and session['loggedin']:
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
    if session and 'loggedin' in session.keys() and session['loggedin']:
        return redirect('/')
    else:
        msg = ''
        if request.method == 'POST' and 'pass' in request.form and 'user' in request.form:
            if not limit_attempts():
                msg = 'Too many login attempts. Please try again later.'
                return render_template('login.html', msg=msg)

            password = request.form['pass']
            user = request.form['user']
            if not re.match(r'^(([a-zA-Z0-9]+)(([-_.][a-zA-Z0-9]+)*))@(([a-zA-Z0-9-]+\.[a-zA-Z]{2,})+)$', user): #avoid sql injection
                msg = "Invalid user input"
                return render_template('login.html',msg=msg)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM accounts WHERE email = %s', (user,))
            account = cursor.fetchone()

            if account and bcrypt.checkpw(password.encode('utf-8'), account['password']):
                session.permanent = True
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
@app.route('/admin/change/<int:user_id>', methods=['GET', 'POST'])
def change_role(user_id):
    if session and 'loggedin' in session.keys() and session['loggedin']:
        if user_id:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (session['id'], ))
            account = cursor.fetchone()
            if account['admin'] == 1:  
                cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (user_id, ))
                target =cursor.fetchone()
                if target:
                    newRole = not target['admin']
                    if target['admin']==0:
                        cursor.execute(f'UPDATE `cssecdv-mp`.accounts SET `admin` ={newRole} WHERE id={user_id}' )
                        mysql.connection.commit()
                        return redirect('/admin')
                    elif target['admin']==1:
                    #check how many admins 
                        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE `admin`=TRUE')
                        adminCount= cursor.fetchall()
                        newRole = not target['admin']
                        if len(adminCount)>1:
                            cursor.execute(f'UPDATE `cssecdv-mp`.accounts SET `admin` ={newRole} WHERE id={user_id}' )
                            mysql.connection.commit()
                            return redirect('/admin')
                        else:
                        #won't flash so user might be clueless why it didn't change
                            flash("We need to have at least one admin!!")
                            return redirect('/admin')
                    else:
                        return redirect('/admin') 
                else:
                    return redirect('/admin')
            else: 
                return redirect('/')  
        else: 
            return redirect('/admin')     
    else:
        return redirect('/login')

@app.route('/admin')
def admin():
    roles=["Regular","Admin"]
    if session and 'loggedin' in session.keys() and session['loggedin']:

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (session['id'], ))
        account = cursor.fetchone()
        user = account['fname']
        if account['admin'] == 1:  
            cursor.execute('SELECT `id`,`email`, `admin` FROM `cssecdv-mp`.accounts')
            records = cursor.fetchall()
            for i in range(len( records)):
                records[i]['role'] = roles[records[i]['admin']]
            return render_template('admin.html',user=user,records=records)
        else: 
            return redirect('/')
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    if session and 'loggedin' in session.keys() and session['loggedin']:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('email', None)
        session.clear()
        return redirect('/login')
    else:
        return redirect('/login')

@app.route('/')
def home():
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE email = %s and id = %s', (session['email'], session['id'],))
        account = cursor.fetchone()
        user = account['fname']  
        return render_template('index.html', user=user, admin=account['admin'])
    else:
        return redirect('/login')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if session and 'loggedin' in session.keys() and session['loggedin']:
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
            if not re.match(r'^(([a-zA-Z0-9]+)(([-_.][a-zA-Z0-9]+)*))@(([a-zA-Z0-9-]+\.[a-zA-Z]{2,})+)$',email): #avoid sql injection
                msg = "Invalid email address!"
                return render_template('reg.html',msg=msg)
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
            elif len(password) < 8:
                msg = "Password should be at least 8 characters!"
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
    #app.run(ssl_context='adhoc',debug=True) #pip install pyopenssl to have https
    #refereence for self-signed SSL: https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https
    app.run(debug=True)
