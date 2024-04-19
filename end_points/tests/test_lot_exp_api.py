import pytest
import requests

API_URL = 'http://localhost:3000/api'

@pytest.fixture
def create_lot_exp():
    # Define the payload for the POST request
    id = '65c8c313b6caf1b43966f1ac'
    payload = {
    "item": 'BECKMAN BICARBONATE',
    "lot_numb": 'test_bench',
    "expiration": '2024-12-31',
    "quantity": 1,
    }
    # Send a POST request to the UserPush endpoint to create a user
    response = requests.post(f'{API_URL}/lotexp/push/{id}', json=payload)
    
    # Return the user ID
    print(response.json())
    lot_exp_id = response.json()['lot_exp_id']
    yield lot_exp_id
    
    # Teardown: Delete the user after the test
    requests.delete(f'{API_URL}/lotexp/del/{lot_exp_id}/')

def test_lotexp_push(create_lot_exp):
    lot_exp_id = create_lot_exp
    assert lot_exp_id is not None


def test_lotexp_get():
    # Send a GET request to fetch the user
    response = requests.get(f'{API_URL}/lotexp/get/')
    actual_lotexp_data = response.json()
    lotexp = actual_lotexp_data['lotexp']
    assert response.status_code == 200
    assert 'lotexp' in actual_lotexp_data
    assert isinstance(lotexp, list)
    assert len(actual_lotexp_data) > 0
    lotexparray = lotexp[0]
    for PI in lotexp:
        assert '_id' in lotexparray
        assert 'created at' in lotexparray
        assert 'user' in lotexparray
        assert 'item' in lotexparray
        assert 'lot_numb' in lotexparray
        assert 'expiration' in lotexparray
        assert 'quantity' in lotexparray


# def test_lotexp_Put(create_lot_exp):
#     lot_exp_id = create_lot_exp
#     # Create a user first to get its ID
#     # Update user data
#     updated_payload = {
#         "item": 'BECKMAN BICARBONATE',
#         "lot_numb": 'test_bench_right',
#         "expiration": 'test_machine_right',
#         "quantity": 1,
#         }
#     response = requests.put(f'{API_URL}/lotexp/put/{lot_exp_id}', json=updated_payload)

#     assert response.status_code == 200
#     # Fetch the updated user data and verify
#     response = requests.get(f'{API_URL}/lotexp/get/{lot_exp_id}')
#     assert response.status_code == 200
#     assert response.json()['item'] == 'BECKMAN BICARBONATE'
#     assert response.json()['lot_numb'] == 'test_bench_right'
#     assert response.json()['expiration'] == 'test_machine_right'
#     assert response.json()['quantity'] == 1

# def test_lotexp_del(create_lot_exp):
#     # Create a user first to get its ID
#     lot_exp_id = create_lot_exp
#     # Send a DELETE request to delete the user
#     response = requests.delete(f'{API_URL}/lotexp/delete/{lot_exp_id}')

#     # Assert that the status code is 200 (OK)
#     assert response.status_code == 200