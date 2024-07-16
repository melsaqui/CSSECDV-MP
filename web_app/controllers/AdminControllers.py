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
#from flask_bootstrap import Bootstrap4
#bootstrap = Bootstrap4()


mysql = MySQL()

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
            return render_template('admin.html',user=user,records=records)
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

                        return redirect('/admin')
                    
                    elif target['admin']==1 and adminCount<=1:
                        flash("We need to have at least one admin!!",category="error")
                        return redirect('/admin')
                else:
                    #target doesn't exist 
                    flash("User does not exist!!",category="error")
                    return redirect('/admin') 
            else:
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
                return redirect('/admin')
            if not str(target_id).isnumeric():
                flash("Invalid id",category='error')
                return redirect('/admin')
            if target_id!=None and request.method == 'POST' and 'admin-pass' in request.form and 'fname' in request.form and 'lname' in request.form and 'phone' in request.form:   
                fname=request.form['fname']    
                lname=request.form['lname']       
                phone= request.form['phone'] 
                adminpass = request.form['admin-pass']
                cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s and email=%s', (target_id, target_email))
                target =cursor.fetchone()
                if target['admin']==0: # cannot edit other admins
                    if account['admin'] and bcrypt.checkpw(adminpass.encode('utf-8'), account['password']):
                        
                        if not re.match(r'[A-Za-z]+', fname):
                            flash('Error Editing: Invalid Name!',category='error')
                        elif not re.match(r'[A-Za-z]+', lname):
                            flash('Error Editing: Invalid Name!',category='error')
                        elif not re.match(r'^09\d{9}$', phone) and not re.match(r'^[+]{1}(?:[0-9\-\(\)\/\.]\s?){6,15}[0-9]{1}$', phone):
                            flash('Error Editing: Invalid Phone number!',category='error')
                        else:
                            cursor.execute("UPDATE `cssecdv-mp`.accounts SET `fname` =%s, `lname`=%s, `phone` =%s WHERE id=%s and email=%s",(fname,lname,phone,target_id, target_email))
                            mysql.connection.commit()
                            flash('Successfully edited!',category='success')   
                        return redirect('/admin')     
                    else:
                        #wrong password
                        flash("Error Editing: Wrong Password Admin", category='error')   
                        return redirect('/admin')             
                else:
                    #target cannot be admin
                    flash ("Error Editing: You cannot edit a the profile of a fellow admin")  
                    return redirect("/admin")
            else:
                #all values should be entered
                flash("Error Editing: Input all values", category='error')
                return redirect('/admin')
        else:
            #not admin
            return redirect('/')
    else:    
        #not loggedin       
        return redirect("/login")

        