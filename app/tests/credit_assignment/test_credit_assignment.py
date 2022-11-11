
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
        content_type ='application/json',
        headers = admin_login_user.headers,
        json=assignment_data,)
    
    assert response.status_code == 201

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