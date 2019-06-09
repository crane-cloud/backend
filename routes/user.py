from flask import request, jsonify

from models import User
from app import app

@app.route('/signup/', methods=['POST'])
def sign_up():
    """ create new user """

    email = request.get_json()['email']
    password = request.get_json()['password']

    # validate input
    if str(email).strip() and str(password).strip():
        user = User(email, password)
        user.save()

        response = jsonify({
            'id': user.id,
            'email': user.email,
            'password': user.password,
            'date_created': user.date_created
        })

        response.status_code = 201

        return response