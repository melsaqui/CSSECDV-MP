from flask import Blueprint

from controllers.AdminControllers import admin, change_role

admin_bp = Blueprint('admin_bp', __name__)
admin_bp.route('/')(admin)
admin_bp.route('/change/<int:user_id>', methods=['GET', 'POST'])(change_role)

