import json
from wsgiref import headers
from app.tests.credit_assignments import UserBaseTestCase, AdminUserBaseTestCase


def test_admin_login(test_client):
    """
    GIVEN  invalid user creation request object
    WHEN the '/users' page is requested (POST)
    THEN check that the response is valid
    """
    admin_user_client = AdminUserBaseTestCase()
    admin_user_client.create_admin_user(admin_user_client.admin_user_data)
    response = test_client.post(
        '/users/admin_login',
        content_type ='application/json',
        data=json.dumps(admin_user_client.admin_user_data),)
    assert response.status_code == 200

def test_credits_assignment(test_client):

    """
    GIVEN  user and admin creation when user and admin already exist
    WHEN the '/credit_assignment' page is requested (POST)
    THEN check that the response is valid
    """

    #create user
    user_client = UserBaseTestCase()
    user = user_client.create_user(user_client.user_data)
    user_id = user.id

    #create admin and get token
    admin_user_client = AdminUserBaseTestCase()
    admin_user_client.create_admin_user(admin_user_client.admin_user_data)
    response = test_client.post(
        '/users/admin_login',
        content_type ='application/json',
        data=json.dumps(admin_user_client.admin_user_data),)
    response_data = response.get_json()
    
    admin_token = response_data["data"]["access_token"]
    
    #assign credits
    header = {'Authorization': 'Bearer ' + admin_token}
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(user_id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = header,
        json=assignment_data,)
    
    assert response.status_code == 201

def test_initial_user_credit_assignment_amount(test_client):

    """
    GIVEN  user and admin creation when user and admin already exist, and user has no credits
    WHEN the '/credit/{user_id}' page is requested (GET)
    THEN check that the user has been assigned the correct amount of credits
    """

    #create user
    user_client = UserBaseTestCase()
    user = user_client.create_user(user_client.user_data)
    user_id = user.id

    #create admin and get token
    admin_user_client = AdminUserBaseTestCase()
    admin_user_client.create_admin_user(admin_user_client.admin_user_data)
    response = test_client.post(
        '/users/admin_login',
        content_type ='application/json',
        data=json.dumps(admin_user_client.admin_user_data),)
    response_data = response.get_json()
    
    admin_token = response_data["data"]["access_token"]
    
    #assign credits
    header = {'Authorization': 'Bearer ' + admin_token}
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(user_id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = header,
        json=assignment_data,)

    #check user credit amount
    
    header = {'Authorization': 'Bearer ' + admin_token}
    response = test_client.get(
        '/credit/{}'.format(user_id),
        content_type ='application/json',
        headers = header)
    response_data = response.get_json()
    credit_amount = response_data["data"]["credit"]["amount"]
    assert credit_amount ==100

def test_user_credit_assignment_amount(test_client):

    """
    GIVEN  user and admin creation when user and admin already exist, and user has credits
    WHEN the '/credit/{user_id}' page is requested (POST)
    THEN check that the user has been assigned the correct amount of credits
    """

    #create user
    user_client = UserBaseTestCase()
    user = user_client.create_user(user_client.user_data)
    user_id = user.id

    #create admin and get token
    admin_user_client = AdminUserBaseTestCase()
    admin_user_client.create_admin_user(admin_user_client.admin_user_data)
    response = test_client.post(
        '/users/admin_login',
        content_type ='application/json',
        data=json.dumps(admin_user_client.admin_user_data),)
    response_data = response.get_json()
    
    admin_token = response_data["data"]["access_token"]
    
    #assign credits
    header = {'Authorization': 'Bearer ' + admin_token}
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(user_id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = header,
        json=assignment_data,)

    #assign credits again
    header = {'Authorization': 'Bearer ' + admin_token}
    assignment_data = {'amount':50, 'description': 'test', 'user_id':'{}'.format(user_id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = header,
        json=assignment_data,)

    #check user credit amount
    header = {'Authorization': 'Bearer ' + admin_token}
    response = test_client.get(
        '/credit/{}'.format(user_id),
        content_type ='application/json',
        headers = header)
    response_data = response.get_json()
    credit_amount = response_data["data"]["credit"]["amount"]
    assert credit_amount ==150  