from flask import request, jsonify, Blueprint

from models.user import User

# user blueprint
user_bp = Blueprint('user', __name__)

@user_bp.route('/register/', methods=['POST'])
def register():
    """ create new user """

    email = request.get_json()['email']
    username = request.get_json()['username']
    password = request.get_json()['password']

    # validate input
    if str(email).strip() and str(password).strip():
        user = User(email, username, password)
        user.save()

        response = jsonify({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'password': user.password,
            'date_created': user.date_created
        })

        response.status_code = 201

        return response