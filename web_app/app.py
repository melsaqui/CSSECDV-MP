from flask import Flask, render_template, request, redirect, session, flash, url_for,jsonify
import logging
from flask_migrate import Migrate
from routes.auth_bp import auth_bp
from routes.admin_bp import admin_bp
from routes.user_bp import user_bp
from datetime import timedelta
from flask_mysqldb import MySQL
import traceback
from flask_bootstrap import Bootstrap4
bootstrap = Bootstrap4()
import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__,template_folder='templates')
from flask_mysqldb import MySQL
app.permanent_session_lifetime = timedelta(minutes=30) #set lifetime session to 30 minute

mysql = MySQL(app)

app.config.from_object('config')
bootstrap.init_app(app)

#db.init_app(app)
#migrate = Migrate(app, db)
#app.logger.setLevel(logging.INFO)  # Set log level to INFO
#handler = logging.FileHandler('app.log')  # Log to a file
#app.logger.addHandler(handler)
logger = logging.getLogger(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp,url_prefix="/admin")
app.register_blueprint(user_bp,url_prefix="/user")

app.errorhandler(Exception)
def handle_exception(e):
    # Log the exception
    logger.exception("An error occurred")
    
    # If in debug mode, return the stack trace
    if app.debug:
        print(traceback.format_exc()) #show in console
        return (traceback.format_exc())
    else:
        # If not in debug mode, return a generic error message
        return "<h1>Soryy, An internal error occurred<h1>", 500

if __name__ == '__main__':
    app.run(ssl_context=('abc.crt','abc.key'))