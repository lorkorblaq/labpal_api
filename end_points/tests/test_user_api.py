import pytest
import requests

API_URL = 'http://localhost:3000/api'

@pytest.fixture
def create_user():
    # Define the payload for the POST request
    payload = {
        'firstname': 'John',
        'lastname': 'Doe',
        'email': 'John.Doe@exakkmple.com',
        'image': 'https://example.com/image.jpg',
        'title': 'Software Engineer',
        'org': 'Example Organization',
        'mobile': 1234567890,
        'address': '123 Example Street',
        'password': 'password123'
    }
    
    # Send a POST request to the UserPush endpoint to create a user
    response = requests.post(f'{API_URL}/user/push/', json=payload)
    assert response.status_code == 200
    
    # Return the user ID
    yield response.json()['user_id']
    
    # Teardown: Delete the user after the test
    requests.delete(f'{API_URL}/user/del/{response.json()["user_id"]}/')


# Replace 'YOUR_API_URL' with the base URL of your Flask application
# Example test for the UserPush endpoint
def test_UserPush(create_user):
    user_id = create_user
    assert user_id is not None
# Add more tests for other endpoints as needed


def test_get_user(create_user):
    # Create a user first to get its ID
    user_id = create_user
    user_id = str(user_id)
    # Send a GET request to fetch the user
    response = requests.get(f'{API_URL}/user/get/{user_id}')
    assert response.status_code == 200
    actual_user_data = response.json()
    # Assert that the response contains the expected user data
    
    # expected_user_data = {
    #     'id': user_id,
    #     'firstname': 'John',
    #     'lastname': 'Doe',
    #     'email': 'John.Doe@example.com',
    #     'title': 'Software Engineer',
    #     'org': 'Example Organization',
    #     'mobile': 1234567890,
    #     'address': '123 Example Street',
    #     'image': 'https://example.com/image.jpg',
    # }
    # assert response.json() == expected_user_data

def test_get_all_users():
    # Send a GET request to fetch all users
    response = requests.get(f'{API_URL}/users/get/')
    assert response.status_code == 200

    # Assert that the response contains a list of users
    assert 'users' in response.json()
    users = response.json()['users']
    assert isinstance(users, list)
    assert len(users) > 0
    for user in users:
        assert 'id' in user
        assert 'firstname' in user
        assert 'lastname' in user
        assert 'email' in user
        assert 'image' in user
        assert 'title' in user
        assert 'org' in user
        assert 'mobile' in user
        assert 'address' in user

def test_UserPut(create_user):
    # Create a user first to get its ID
    user_id = create_user
    # Update user data
    updated_payload = {
        'firstname': 'Jane',
        'lastname': 'Smith',
        'email': 'jane.smith@example.com',
        'title': 'Software Engineer',
        'org': 'Example Organization',
        'mobile': 1234567890,
        'address': '123 Example Street'
    }
    response = requests.put(f'{API_URL}/user/put/{user_id}', json=updated_payload)
    assert response.status_code == 200

    # Fetch the updated user data and verify
    response = requests.get(f'{API_URL}/user/get/{user_id}')
    assert response.status_code == 200
    assert response.json()['title'] == 'Software Engineer'
    assert response.json()['org'] == 'Example Organization'
    assert response.json()['mobile'] == 1234567890
    assert response.json()['address'] == '123 Example Street'

def test_UserDel(create_user):
    # Create a user first to get its ID
    user_id = create_user
    # Send a DELETE request to delete the user
    response = requests.delete(f'{API_URL}/user/del/{user_id}')

    # Assert that the status code is 200 (OK)
    assert response.status_code == 200