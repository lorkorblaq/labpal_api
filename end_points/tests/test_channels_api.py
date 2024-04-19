import pytest
from flask import Flask
from flask.testing import FlaskClient
import requests
from datetime import datetime, timedelta

API_URL = 'http://localhost:3000/api'

@pytest.fixture
def create_channel():
    # Define the payload for the POST request
    id = '65c8c313b6caf1b43966f1ac'
    payload = {
    "item": 'BECKMAN BICARBONATE',
    "direction": 'test_to',
    "lot_numb": '2323',
    "location": 'test_location',
    "quantity": 1,
    "description": 'test_description'
    }
    # Send a POST request to the UserPush endpoint to create a user
    response = requests.post(f'{API_URL}/channel/push/{id}', json=payload)
    assert response.status_code == 200
    
    # Return the user ID
    print(response.json())
    channel_id = response.json()['channel_id']
    yield channel_id
    
    # Teardown: Delete the user after the test
    requests.delete(f'{API_URL}/piu/del/{channel_id}/')

# Example test for the channel endpoint
def test_channel_push(create_channel):
    channel_id = create_channel
    assert channel_id is not None

def test_channel_get():
    # Send a GET request to fetch the user
    response = requests.get(f'{API_URL}/channels/get/')
    actual_channel_data = response.json()
    channels_data = actual_channel_data['channels']
    assert response.status_code == 200
    assert 'channels' in actual_channel_data
    assert isinstance(channels_data, list)
    assert len(actual_channel_data) > 0
    channel_array = channels_data[0]
    for channel in channels_data:
        assert '_id' in channel_array
        assert 'created at' in channel_array
        assert 'user' in channel_array
        assert 'lot_numb' in channel_array
        assert 'direction' in channel_array
        assert 'location' in channel_array
        assert 'quantity' in channel_array
        assert 'description' in channel_array


def test_channel_Put(create_channel):
    channel_id = create_channel
    # Create a user first to get its ID
    # Update user data
    updated_payload = {
        "item": 'BECKMAN BICARBONATE',
        "direction": 'test_from',
        "lot_number": '2323',
        "quantity": 1,
        "description": 'test_description_right',
        }
    response = requests.put(f'{API_URL}/channel/put/{channel_id}', json=updated_payload)

    assert response.status_code == 200
    # Fetch the updated user data and verify
    response = requests.get(f'{API_URL}/channel/get/{channel_id}')
    assert response.status_code == 200
    assert response.json()['item'] == 'BECKMAN BICARBONATE'
    assert response.json()['direction'] == 'test_from'
    assert response.json()['lot_numb'] == '2323'
    assert response.json()['quantity'] == 1
    assert response.json()['description'] == 'test_description_right'

def test_channel_del(create_channel):
    # Create a user first to get its ID
    channel_id = create_channel
    # Send a DELETE request to delete the user
    response = requests.delete(f'{API_URL}/channel/delete/{channel_id}')

    # Assert that the status code is 200 (OK)
    assert response.status_code == 200
