
def test_credits_assignment(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist
    WHEN the '/credit_assignment' page is requested (POST)
    THEN check that the response is valid
    """
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type='application/json',
        headers=admin_login_user.headers,
        json=assignment_data
    )
    response_data = response.get_json()
    assert response.status_code == 201
    assert response_data['status'] == "success"
    assert "Credit for user_id" in response_data['message']

def test_initial_user_credit_assignment_amount(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist, and user has no credits
    WHEN the '/credit/{user_id}' page is requested (GET)
    THEN check that the user has been assigned the correct amount of credits
    """
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)

    #check user credit amount
    response = test_client.get(
        '/credit/{}'.format(login_user.user.id),
        content_type ='application/json',
        headers = login_user.headers)
    response_data = response.get_json()
    credit_amount = response_data["data"]["credit"]["amount"]
    assert credit_amount ==100

def test_user_credit_assignment_amount(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist, and user has credits
    WHEN the '/credit/{user_id}' page is requested (POST)
    THEN check that the user has been assigned the correct amount of credits
    """
    
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)
    
        #assign credits
    assignment_data = {'amount':50, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)

     #check user credit amount
    response = test_client.get(
        '/credit/{}'.format(login_user.user.id),
        content_type ='application/json',
        headers = login_user.headers)
    response_data = response.get_json()
    credit_amount = response_data["data"]["credit"]["amount"]
    assert credit_amount ==150

def test_credit_assignment_amount_string(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist
    WHEN the '/credit_assignment' page is requested (POST) with string amount
    THEN check that the correct error is output
    """
    #assign credits
    assignment_data = {'amount':'ffdsff', 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)
    assert response.status_code == 400

def test_credit_assignment_incorrect_non_existing_user_id(test_client, admin_login_user):

    """
    GIVEN  user and admin creation when user and admin already exist
    WHEN the '/credit_assignment' page is requested (POST) with non-existant user id
    THEN check that the correct error is output
    """
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'11111'}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)
    assert response.status_code == 400

def test_credit_assignment_unauthorized_user(test_client, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist
    WHEN the '/credit_assignment' page is requested (POST) with unauthorized user
    THEN check that the correct error is output
    """
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = login_user.headers,
        json=assignment_data,)
    assert response.status_code == 403

def test_credits_assignment_invalid_token(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist
    WHEN the '/credit_assignment' page is requested (POST)
    THEN check that the response is valid
    """
    #assign credits
    header = {'Authorization': 'Bearer 1111111111'}
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = header,
        json=assignment_data,)
    
    assert response.status_code == 422


def test_credits_assignment_detail(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist and users have credits
    WHEN the users have been assigned credits '/credit_assignment/{user_id}' page is requested (GET)
    THEN check that the response is valid
    """
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)

    #get credits
    response = test_client.get(
        '/credit_assignment/{}'.format(login_user.user.id),
        content_type ='application/json',
        headers = login_user.headers)

    assert response.status_code == 200


def test_credits_assignment_detail_invalid_token(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist and users have credits
    WHEN the users have been assigned credits '/credit_assignment/{user_id}' page is requested (GET) with invalid token
    THEN check that the response is valid
    """
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)

    #get credits
    header = {'Authorization': 'Bearer 1111111111'}
    response = test_client.get(
        '/credit_assignment/{}'.format(login_user.user.id),
        content_type ='application/json',
        headers = header)

    assert response.status_code == 422

def test_credits_assignment_detail_unauthorized_user(test_client, admin_login_user, login_user):

    """
    GIVEN  user and admin creation when user and admin already exist and users have credits
    WHEN the users have been assigned credits '/credit_assignment/{user_id}' page is requested (GET) with invalid token
    THEN check that the response is valid
    """
    #assign credits
    assignment_data = {'amount':100, 'description': 'test', 'user_id':'{}'.format(login_user.user.id)}
    response = test_client.post(
        '/credit_assignment',
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)

    #get credits
    non_existing_user = {'1111111111'}
    response = test_client.get(
        '/credit_assignment/{}'.format(non_existing_user),
        content_type ='application/json',
        headers = admin_login_user.headers)

    assert response.status_code == 404