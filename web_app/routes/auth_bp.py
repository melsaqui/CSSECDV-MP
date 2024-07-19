from flask import Blueprint

from controllers.AuthControllers import home, login,register,logout

auth_bp = Blueprint('auth_bp', __name__)

auth_bp.route('/')(home)
auth_bp.route('/login', methods=['GET', 'POST'])(login)
auth_bp.route('/register', methods=['GET', 'POST'])(register)
auth_bp.route('/logout')(logout)




