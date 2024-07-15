from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_migrate import Migrate
from routes.auth_bp import auth_bp
from routes.admin_bp import admin_bp

import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
from flask_mysqldb import MySQL

mysql = MySQL(app)

app.config.from_object('config')

#db.init_app(app)
#migrate = Migrate(app, db)

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp,url_prefix="/admin")


if __name__ == '__main__':
    app.debug = True
    app.run(ssl_context=('abc.crt','abc.key'))