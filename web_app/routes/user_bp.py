from flask import Blueprint

from controllers.ProfileControllers import profile,edit

user_bp = Blueprint('user_bp', __name__)

user_bp.route('/')(profile)
user_bp.route('/edit',methods=["GET","POST"])(edit)