import os
import time
from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_mysqldb import MySQL
import MySQLdb.cursors
#import bcrypt
import re
from werkzeug.utils import secure_filename
import sys
#from datetime import timedelta

mysql = MySQL()

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
def get_count_admin():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE `admin`=TRUE')
    count = len(cursor.fetchall())
    return count
def change_role(user_id):
    if session and 'loggedin' in session.keys() and session['loggedin']:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (session['id'], ))
        account = cursor.fetchone()
        if account['admin'] == 1: 
            roles=["Regular","Admin"]
 
            if user_id and user_id!="":
                cursor.execute('SELECT * FROM `cssecdv-mp`.accounts WHERE id =%s', (user_id, ))
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