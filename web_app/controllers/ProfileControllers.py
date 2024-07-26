import os
import time
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
import bcrypt
import re
from werkzeug.utils import secure_filename
import sys
from datetime import timedelta,datetime

#from flask_bootstrap import Bootstrap4
#bootstrap = Bootstrap4()
import pandas as pd
import logging

mysql = MySQL()
logger = logging.getLogger(__name__)

def profile():
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE email = %s and id = %s', (session['email'], session['id'],))
        account = cursor.fetchone()
        return render_template('profile.html',admin=account['admin'],info=account)
    else:
        return redirect('/login')
    
def valid_date(date): #valid considering february and 30 and 31 days months
    date_split = str(date).split('-')
    #year-mm-dd
    thirty_one = [1,3,5,7,8,10,12]
    if int(date_split[1])==2: #if february
        
        if int(date_split[2])<=28: #if date <=28 valid no matter what
            return True
        elif((int(date_split[0]) % 400 == 0) or (int(date_split[0]) % 100 != 0) and (int(date_split[0]) % 4 == 0)) and int(date_split[2])<=29 :
            return True
        else:
            return False          
    elif (int(date_split[1]) in thirty_one) and int(date_split[2])<=31:
        return True
    elif not(int(date_split[1]) in thirty_one) and int(date_split[2])<=30:
        return True
    else: 
        return False
    
def edit():
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        #For the sake of detailed logging
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE email = %s and id = %s', (session['email'], session['id'],))
        prev_details = cursor.fetchone()
        if request.method == 'POST' and  'email' in request.form and 'fname' in request.form and 'lname' in request.form and 'phone' in request.form and'bday' in request.form:
            email=request.form['email']
            lname =request.form['lname']
            fname =request.form['fname']
            phone = request.form['phone']
            bday =request.form['bday']
            if email!=session['email']:
                flash("You can only edit you profile. If you are an admin go to admin panel", category ="error")
                logger.info(f"Invalid access to edit {email} in this page")

                return redirect('/user')
            elif not re.match(r'^([A-Za-z]\s*)+$', fname):
                flash('Invalid Name!',category ='error')
                logger.info("Invalid name format")
            elif not re.match(r'^([A-Za-z]\s*)+$', lname):
                flash('Invalid Name!',category ='error')
                logger.info("Invalid name format")

            elif not re.match(r'^09\d{9}$', phone) and not re.match(r'^[+]{1}(?:[0-9\-\(\)\/\.]\s?){6,15}[0-9]{1}$', phone):
                flash("Invalid phone number",category ='error')
                logger.info("Invalid phone format")

            elif not re.match(r'^((19|20)\d{2})-((1[0-2])|(0[1-9]))-(([0-2]\d)|(3[0-1]))$',bday):
                flash(f"Invalid birthday {bday}",category ='error')
                logger.info("Invalid date format")


            elif not valid_date(bday):
                flash(f"Invalid birthday {bday}",category ='error') 
                logger.info("Invalid date")
              
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("UPDATE `cssecdv-mp`.accounts SET `fname` =%s, `lname`=%s, `phone` =%s, `birthday`=%s WHERE id=%s and email=%s",(fname,lname,phone,bday,session['id'], session['email']))
                mysql.connection.commit()
              
                flash("Successfully updated", category='success')
                logger.info(f"Successfully edited profile of {email}")
                if prev_details['fname'] != fname:
                    logger.info(f"Changed first name to {fname}")
                if prev_details['lname'] != lname:
                    logger.info(f"Changed last name to {lname}")
                if prev_details['phone'] != phone:
                    logger.info(f"Changed phone to {phone}")
                if str(prev_details['birthday']) != str(bday):
                    logger.info(f"Changed bday to {bday}")



            return redirect('/user')
                                
        else:
            flash("Error: Something Happened",category='error')
            logger.error("Something Happened")
            return redirect('/user')

    else: 
        return redirect('/login')
