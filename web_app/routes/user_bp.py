from flask import Blueprint
from controllers.ProfileControllers import profile, edit, upload_profile_picture

user_bp = Blueprint('user_bp', __name__)

user_bp.route('/')(profile)
user_bp.route('/edit', methods=["GET", "POST"])(edit)
user_bp.route('/upload-profile-picture', methods=['POST'])(upload_profile_picture)