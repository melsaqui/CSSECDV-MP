import os
import time
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import re
from werkzeug.utils import secure_filename
import sys
import logging
from datetime import timedelta
logger = logging.getLogger(__name__)
mysql = MySQL()
login_attempts = {}
#MYSQL_CURSORCLASS= 'DictCursor'

# Constants for brute force protection
MAX_ATTEMPTS = 5
BLOCK_DURATION = 300  # 5 minutes
TIME_FRAME = 600  # 10 minutes

#index page
def home():
    #raise Exception("Test purposes")
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE email = %s and id = %s', (session['email'], session['id'],))
        account = cursor.fetchone()
        user = account['fname']  
        return render_template('index.html', user=user, admin=account['admin'])
    else:
        return redirect('/login')
       
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
                logger.info("Attempted to create an existing account")

            elif not re.match(r'^(([a-zA-Z0-9]+)(([-_.][a-zA-Z0-9]+)*))@(([a-zA-Z0-9-]+\.[a-zA-Z]{2,})+)$', email):
                msg = 'Invalid email address!'
                logger.info("Invalid email format")
            elif not re.match(r'^([A-Za-z]\s*)+$', fname):
                msg = 'Invalid Name!'
                logger.info("Invalid name format")
            elif not re.match(r'^([A-Za-z]\s*)+$', lname):
                msg = 'Invalid Name!'
                logger.info("Invalid name format")
            elif not re.match(r'^09\d{9}$', phone) and not re.match(r'^[+]{1}(?:[0-9\-\(\)\/\.]\s?){6,15}[0-9]{1}$', phone):
                msg = "Invalid phone number"
                logger.info("Invalid phone format")
            elif len(password) < 8:
                msg = "Password should be at least 8 characters!"
                logger.info("Invalid password format")
            elif password != reppass:
                msg = "Passwords not matching"
                logger.info("Passwords not matching")

            elif not email or not password or not phone or not reppass or not fname or not lname:
                msg = 'Please fill out the form!'
                logger.info("incomplete form")
            else:
                cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s, %s, %s, False,NULL,NULL)', (fname, lname, email, phone, hashed))
                mysql.connection.commit()
                msg = 'You have successfully registered!'
                logger.info(f"User {email} created")

        elif request.method == 'POST':
            msg = 'Please fill out the form!'
            logger.info("Blank form")

        return render_template('reg.html', msg=msg)
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
def login():
    if session and 'loggedin' in session.keys() and session['loggedin']:
        return redirect('/')
    else:
        msg = ''
        if request.method == 'POST' and 'pass' in request.form and 'user' in request.form:
            if not limit_attempts():
                msg = 'Too many login attempts. Please try again later.'
                logger.info(f"Invalid login. Too many attempts" )

                return render_template('login.html', msg=msg)

            password = request.form['pass']
            user = request.form['user']
            if not re.match(r'^(([a-zA-Z0-9]+)(([-_.][a-zA-Z0-9]+)*))@(([a-zA-Z0-9-]+\.[a-zA-Z]{2,})+)$', user): #avoid sql injection
                msg = "Invalid user input"
                logger.info("Invlid email format")
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
                logger.info(f"User {session['email']} is logged in" )
                return redirect('/')
            else:
                msg = 'Incorrect username / password!'
                logger.info(f"Invalid login" )
                # Increment failed attempts for the current IP
                client_ip = request.remote_addr
                if client_ip in login_attempts:
                    login_attempts[client_ip][0] += 1
                    
                else:
                    login_attempts[client_ip] = [1, time.time()]

        return render_template('login.html', msg=msg)    
def logout():
    if session and 'loggedin' in session.keys() and session['loggedin']:
        session.pop('loggedin', None)
        logger.info(f"{session['email']} logged out")
        session.pop('id', None)
        session.pop('email', None)
        session.clear()
        return redirect('/login')
    else:
        return redirect('/login')
