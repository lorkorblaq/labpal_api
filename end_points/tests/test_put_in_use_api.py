import pytest
from flask import Flask
from flask.testing import FlaskClient
import requests
from datetime import datetime, timedelta

API_URL = 'http://localhost:3000/api'

@pytest.fixture
def create_piu():
    # Define the payload for the POST request
    id = '65c8c313b6caf1b43966f1ac'
    payload = {
    "item": 'BECKMAN BICARBONATE',
    "bench": 'test_bench',
    "machine": 'test_bench',
    "quantity": 1,
    "description": 'test_description'
    }
    # Send a POST request to the UserPush endpoint to create a user
    response = requests.post(f'{API_URL}/piu/push/{id}', json=payload)
    assert response.status_code == 200
    
    # Return the user ID
    print(response.json())
    piu_id = response.json()['piu_id']
    yield piu_id
    
    # Teardown: Delete the user after the test
    requests.delete(f'{API_URL}/piu/del/{piu_id}/')

def test_PIU_push(create_piu):
    piu_id = create_piu
    assert piu_id is not None


def test_PIU_get():
    # Send a GET request to fetch the user
    response = requests.get(f'{API_URL}/piu/get/')
    actual_PIU_data = response.json()
    PIU = actual_PIU_data['piu']
    assert response.status_code == 200
    assert 'piu' in actual_PIU_data
    assert isinstance(PIU, list)
    assert len(actual_PIU_data) > 0
    PIUarray = PIU[0]
    for PI in PIU:
        assert '_id' in PIUarray
        assert 'created at' in PIUarray
        assert 'user' in PIUarray
        assert 'item' in PIUarray
        assert 'bench' in PIUarray
        assert 'machine' in PIUarray
        assert 'quantity' in PIUarray
        assert 'description' in PIUarray


def test_put_in_use_Put(create_piu):
    piu_id = create_piu
    # Create a user first to get its ID
    # Update user data
    updated_payload = {
        "item": 'BECKMAN BICARBONATE',
        "bench": 'test_bench_right',
        "machine": 'test_machine_right',
        "quantity": 1,
        "description": 'test_description_right',
        }
    response = requests.put(f'{API_URL}/piu/put/{piu_id}', json=updated_payload)

    assert response.status_code == 200
    # Fetch the updated user data and verify
    response = requests.get(f'{API_URL}/piu/get/{piu_id}')
    assert response.status_code == 200
    assert response.json()['item'] == 'BECKMAN BICARBONATE'
    assert response.json()['bench'] == 'test_bench_right'
    assert response.json()['machine'] == 'test_machine_right'
    assert response.json()['quantity'] == 1
    assert response.json()['description'] == 'test_description_right'

def test_PIU_del(create_piu):
    # Create a user first to get its ID
    piu_id = create_piu
    # Send a DELETE request to delete the user
    response = requests.delete(f'{API_URL}/piu/delete/{piu_id}')

    # Assert that the status code is 200 (OK)
    assert response.status_code == 200