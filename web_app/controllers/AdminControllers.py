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

import pandas as pd
from .ProfileControllers import valid_date
import logging

logger = logging.getLogger(__name__)

# Constants for brute force protection
MAX_ATTEMPTS = 5
BLOCK_DURATION = 300  # 5 minutes
TIME_FRAME = 600  # 10 minutes
blocked_actions =0
admin_actions=3
pass_attempts = {}

mysql = MySQL()
def limit_attempts():
    client_ip = request.remote_addr
    current_time = time.time()

    if client_ip in pass_attempts:
        attempts, first_attempt_time = pass_attempts[client_ip]

        if attempts >= MAX_ATTEMPTS:
            if current_time - first_attempt_time < BLOCK_DURATION:
                return False
            else:
                # Reset attempts after block duration
                pass_attempts[client_ip] = [0, current_time]
        elif current_time - first_attempt_time > TIME_FRAME:
            # Reset attempts after the time frame
            pass_attempts[client_ip] = [0, current_time]
    else:
        pass_attempts[client_ip] = [0, current_time]

    return True
def admin():
    roles=["Regular","Admin"]
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (session['id'], ))
        account = cursor.fetchone()
        user = account['fname']
        if account['admin'] == 1:  
            cursor.execute('SELECT * FROM `cssecdv-mp`.accounts')
            records = cursor.fetchall()
            for i in range(len( records)):
                records[i]['role'] = roles[records[i]['admin']]
            df = pd.DataFrame(records)
            df_sort = df.sort_values(by='email')
            sorted_data = df_sort.to_dict(orient='records') # so its not sorted by id less easy to guess user IDs
            return render_template('admin.html',user=user,records= sorted_data)
        else: 
            return redirect('/')
    else:
        return redirect('/login')
def get_count_admin():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE `admin`=TRUE')
    count = len(cursor.fetchall())
    return count

def change_role(user_id,user_email):
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (session['id'], ))
        account = cursor.fetchone()
        if account['admin'] == 1: 
            roles=["Regular","Admin"]
            if request.method == 'POST' and 'admin-pass' in request.form:
                if not limit_attempts():
                    flash('Too many attempts. Please try again later...',category='error')
                    logger.info('Too many failed password attempts. Temporary block from changing rolese')
                    return redirect("/admin")
                adminpass = request.form['admin-pass']
                if not bcrypt.checkpw(adminpass.encode('utf-8'), account['password']):
                    flash("Error: Invalid Password",category="error")
                    logger.info("Invalid Password input")
                    client_ip = request.remote_addr
                    if client_ip in pass_attempts:
                        pass_attempts[client_ip][0] += 1
                    else:
                        pass_attempts[client_ip] = [1, time.time()]
                    return redirect('/admin')
                if user_id and user_id!="":
                    cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s AND email=%s', (user_id,user_email ))
                    target =cursor.fetchone()
                    if target:
                        newRole = not target['admin']
                        adminCount= get_count_admin() #we cannot allow no admins 

                        if target['admin']==0 or (target['admin']==1 and adminCount>1 ):
                            cursor.execute(f'UPDATE `cssecdv-mp`.accounts SET `admin` ={newRole} WHERE id={user_id}' )
                            mysql.connection.commit()
                            flash(f"Successfully updated role of {target['email']} to {roles[newRole]} !", category="success")
                            logger.info(f"Successfully changed role of {target['email']} to {roles[newRole]}")

                            return redirect('/admin')
                    
                        elif target['admin']==1 and adminCount<=1:
                            flash("Error: We need to have at least one admin!!",category="error")
                            logger.info('Failed to change a role due to having no admin if granted request')

                        return redirect('/admin')
                    else:
                        #target doesn't exist 
                        flash("Error: User does not exist!!",category="error")
                        logger.info('Target user does not exist to change role')

                        return redirect('/admin') 
                else:
                    return redirect('/admin')
            else: 
                flash("Error: Enter your password", category="error")
                logger.info('No password input')

                return redirect('/admin')
        else: 
            #not admin
            return redirect('/')     
    else:
        #not loggedin
        return redirect('/login')
    
def edit(target_id,target_email):
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s and email=%s', (session['id'], session['email']))
        account = cursor.fetchone()
        if account['admin'] == 1: 
            if not re.match(r'^(([a-zA-Z0-9]+)(([-_.][a-zA-Z0-9]+)*))@(([a-zA-Z0-9-]+\.[a-zA-Z]{2,})+)$',target_email): #avoid sql injection
                flash("Invalid email address!",category='error')
                logger.info("Invalid email address format")
                return redirect('/admin')
            if not str(target_id).isnumeric():
                flash("Invalid id",category='error')
                logger.info("Invalid regular user ID")
                return redirect('/admin')
            if target_id!=None and request.method == 'POST' and 'admin-pass' in request.form and 'fname' in request.form and 'lname' in request.form and 'phone' in request.form and 'bday' in request.form:
                if not limit_attempts():
                    flash('Too many attempts. Please try again later...',category='error')
                    logger.info("Too many attempts at password input, temporarily blocked from editing")

                    return redirect("/admin")   
                fname=request.form['fname']    
                lname=request.form['lname']       
                phone= request.form['phone'] 
                adminpass = request.form['admin-pass']
                bday =request.form['bday']
                cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s and email=%s', (target_id, target_email))
                target =cursor.fetchone()
                if target['admin']==0: # cannot edit other admins 
                    if account['admin'] and bcrypt.checkpw(adminpass.encode('utf-8'), account['password']):
                        
                        if not re.match(r'^([A-Za-z]\s*)+$', fname):
                            flash('Error Editing: Invalid Name!',category='error')
                            logger.info("Invalid Name format")

                        elif not re.match(r'^([A-Za-z]\s*)+$', lname):
                            flash('Error Editing: Invalid Name!',category='error')
                            logger.info("Invalid Name format")

                        elif not re.match(r'^09\d{9}', phone) and not re.match(r'^[+]{1}(?:[0-9\-\(\)\/\.]\s?){6,15}[0-9]{1}$', phone):
                            flash('Error Editing: Invalid Phone number!',category='error')
                            logger.info("Invalid Phone format")

                        elif not re.match(r'^((19|20)\d{2})-((1[0-2])|(0[1-9]))-(([0-2]\d)|(3[0-1]))$',bday):
                            flash(f"Invalid birthday {bday}",category ='error')
                            logger.info("Invalid date format")

                        elif not valid_date(bday):
                            flash(f"Invalid birthday {bday}",category ='error') 
                            logger.info("Invalid date format")

                        else:
                            cursor.execute("UPDATE `cssecdv-mp`.accounts SET `fname` =%s, `lname`=%s, `phone` =%s, `birthday`=%s WHERE id=%s and email=%s",(fname,lname,phone,bday, target_id, target_email))
                            mysql.connection.commit()
                            flash('Successfully edited!',category='success')  
                            logger.info(f"Edited profile details of {target_email}")
 
                        return redirect('/admin')     
                    else:
                        #wrong password
                        flash("Error Editing: Incorrect Password, Admin", category='error')  
                        logger.info("Invalid Password")
                        client_ip = request.remote_addr
                        if client_ip in pass_attempts:
                            pass_attempts[client_ip][0] += 1
                        else:
                            pass_attempts[client_ip] = [1, time.time()]
                        return redirect('/admin') 
                else:
                    #target cannot be admin
                    flash ("Error Editing: You cannot edit a the profile of a fellow admin")  
                    logger.info("Failed due to target being admin")

                    return redirect("/admin")
            else:
                #all values should be entered
                flash("Error Editing: Input all values", category='error')
                logger.info("IEmpty values")

                return redirect('/admin')
        else:
            #not admin
            return redirect('/')
    else:    
        #not loggedin       
        return redirect("/login")
def reset_pass(target_id, target_email):
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s and email=%s', (session['id'], session['email']))
        account = cursor.fetchone()
        if account['admin'] == 1: 
            if not re.match(r'^(([a-zA-Z0-9]+)(([-_.][a-zA-Z0-9]+)*))@(([a-zA-Z0-9-]+\.[a-zA-Z]{2,})+)$',target_email): #avoid sql injection
                flash("Invalid email address!",category='error')
                return redirect('/admin')
            if not str(target_id).isnumeric():
                flash("Invalid id",category='error')
                return redirect('/admin')
            if target_id!=None and target_email!=None and request.method == 'POST' and 'admin-pass' in request.form and 'nPass' in request.form and 'conf_pass' in request.form:   
                if not limit_attempts():
                    flash('Too many attempts. Please try again later...',category='error')
                    return redirect("/admin")   
                pas = request.form['nPass']
                conf_pass= request.form['conf_pass']
                adminpass = request.form['admin-pass']
                salt = bcrypt.gensalt(rounds=12)
                hashed = bcrypt.hashpw(bytes(pas, 'utf-8'), salt)
                if account['admin'] and bcrypt.checkpw(adminpass.encode('utf-8'), account['password']):

                    cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s and email=%s', (target_id, target_email))
                    target=cursor.fetchone()
                    if target['admin']==0: # cannot edit other admins 
                        if len(pas)<8:
                            flash("Password should be at least 8 characters!","error")
                        elif pas!=conf_pass:
                            flash("Passwords Not Matching!","error")
                        else:
                            cursor.execute("UPDATE `cssecdv-mp`.accounts SET `password` = %s WHERE id=%s and email=%s",(hashed,target_id, target_email))
                            mysql.connection.commit()
                            flash(f'Successfully Reset, don\t forget to notify {target_email} of new password!',category='success')     
                        return redirect('/admin')
                    else:
                        flash("Error: You cannot change another admin's password!!", category="error")
                        return redirect('/admin')

                else:
                    flash("Error: Incorrect Password", category="error")
                    client_ip = request.remote_addr
                    if client_ip in pass_attempts:
                        pass_attempts[client_ip][0] += 1
                    else:
                        pass_attempts[client_ip] = [1, time.time()]
                    return redirect('/admin')
        else:
            return redirect('/')
    else:
        return redirect('/login')

        