from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import re

app = Flask(__name__,template_folder='views')
    
app.secret_key = 'your secret key'
 
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Lacsapcshs2020*'
app.config['MYSQL_DB'] = 'cssecdv-mp'
app.config['MYSQL_CURSORCLASS'] = "DictCursor"

mysql = MySQL(app)
#@app.route('/login')
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect('/login')
@app.route('/')
def home():
    if session['loggedin']:
        user=session['email']
        return render_template('index.html',user =user)
    else:
        return redirect('/login')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'pass' in request.form and 'user' in request.form:
        password = request.form['pass']
        user=request.form['user']
        
        #salt = bcrypt.gensalt(rounds=20)
        #hashed_password = bcrypt.hashpw(bytes(password, 'utf-8'), salt)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE email = % s', (user, ))
        account = cursor.fetchone()
        if account:
            if bcrypt.checkpw(bytes(password, 'utf-8'), account['password']):
                session['loggedin'] = True
                session['id'] = account['id']
                session['email'] = account['email']
                msg = 'Logged in successfully !'
                
                return render_template('index.html',user = account['email'])
            else:
                msg = 'Incorrect username / password !'

        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html',msg=msg)
@app.route('/register', methods = ['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'psw' in request.form and 'email' in request.form:
        fname = request.form['fname']
        lname = request.form['lname']
        password = request.form['psw']
        reppass = request.form['psw-repeat']
        email = request.form['email']
        phone = request.form['phone']
        salt = bcrypt.gensalt(rounds=20)
        hashed = bcrypt.hashpw(bytes(password, 'utf-8'), salt)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z]+', fname):
            msg = 'Invalid Name!'
        elif not re.match(r'[A-Za-z]+', lname):
            msg = 'Invalid Name!'
        elif not re.match(r'^09\d{9}',phone):
            msg= "invalid phone number"
        elif password!=reppass:
            msg= "Passwords not matching"
        elif not email or not password or not phone or not reppass or not fname or not lname:
            msg = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO accounts VALUES (NULL, % s, % s, % s, %s, %s,False)', (fname, lname, email, phone,(hashed) ))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
    return render_template('reg.html', msg = msg)
   # return render_template('reg.html')
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)