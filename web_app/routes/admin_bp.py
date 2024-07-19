from flask import Blueprint

from controllers.AdminControllers import admin, change_role, edit, reset_pass

admin_bp = Blueprint('admin_bp', __name__)
admin_bp.route('/')(admin)
admin_bp.route('/change-role/<int:user_id>&<user_email>', methods=['GET', 'POST'])(change_role)
admin_bp.route('/<int:target_id>&<target_email>/edit', methods = ['POST'])(edit)
admin_bp.route('/<int:target_id>/reset-pass/<target_email>', methods = ['POST'])(reset_pass)
