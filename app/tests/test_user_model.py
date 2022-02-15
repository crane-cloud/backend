def test_create_user_with_fixture(new_user):
    assert new_user.email == 'test_email@testdomain.com'
    assert new_user.password != 'test_password'
    assert new_user.name == 'test_name'


