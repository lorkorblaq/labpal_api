import requests

base_url = "http://127.0.0.1:5000/api"

def test_user_api():
    try:
        user_data = {"name": "Jngjj", "email": "jnkjo.dobk@xaple.com", "password": "passwrd123"}

        # Test creating a new user
        response = requests.post(f"{base_url}/user/push/", json=user_data)
        response.raise_for_status()
        print("User Creation: Passed")

        # Test getting all users
        response = requests.get(f"{base_url}/users/get")
        response.raise_for_status()
        print("Get All Users: Passed")

        # Assuming user_id is the ID of the user created in the first step
        user_id = 1

        # Test updating a user
        update_data = {"name": "John Dower Updated"}
        response = requests.put(f"{base_url}/user/put/{user_id}/", json=update_data)
        response.raise_for_status()
        print("Update User: Passed")

        # Test deleting a user
        response = requests.delete(f"{base_url}/user/del/{user_id}/")
        response.raise_for_status()
        print("Delete User: Passed")

    except requests.exceptions.RequestException as e:
        print(f"Error in test_user_api: {e}")

def test_channel_api():
    try:
        user_id = 1
        channel_id = 1

        channel_data = {
            "user_id": user_id,
            "item": "Free T4",
            "lot": "422789",
            "direction": "to",
            "location": "Warehouse",
            "quantity": 10,
            "description": "Test Channel"
        }

        # Test creating a new channel
        response = requests.post(f"{base_url}/channel/push/{user_id}", json=channel_data)
        response.raise_for_status()
        print("Create Channel: Passed")

        # Test getting all channels
        response = requests.get(f"{base_url}/channels/get/")
        response.raise_for_status()
        print("Get All Channels: Passed")

        # Assuming channelId is the ID of the channel created in the first step
        channel_id = 1

        # Test updating a channel
        update_data = {"quantity": 20}
        response = requests.put(f"{base_url}/channel/put/{channel_id}/", json=update_data)
        response.raise_for_status()
        print("Update Channel: Passed")

        # Test deleting a channel
        response = requests.delete(f"{base_url}/channel/delete/{channel_id}/")
        response.raise_for_status()
        print("Delete Channel: Passed")

    except requests.exceptions.RequestException as e:
        print(f"Error in test_channel_api: {e}")

def test_put_in_use_api():
    try:
        user_id = 1

        put_in_use_data = {
            "item": "Free t4",
            "lot": "422789",
            "bench": "endo",
            "machine": "Dxc700",
            "quantity": 5,
            "description": "Test Put in use"
        }

        # Test putting an item in use
        response = requests.post(f"{base_url}/pis/push/{user_id}/", json=put_in_use_data)
        response.raise_for_status()
        print("Put Item in Use: Passed")

        # Test getting all items put in use
        response = requests.get(f"{base_url}/pis/get/")
        response.raise_for_status()
        print("Get All Items Put in Use: Passed")

        # Assuming pisId is the ID of the item put in use created in the first step
        pisId = 1

        # Test updating an item put in use
        update_data = {"quantity": 10}
        response = requests.put(f"{base_url}/pis/put/{pisId}/", json=update_data)
        response.raise_for_status()
        print("Update Item Put in Use: Passed")

        # Test deleting an item put in use
        response = requests.delete(f"{base_url}/pis/delete/{pisId}/")
        response.raise_for_status()
        print("Delete Item Put in Use: Passed")

    except requests.exceptions.RequestException as e:
        print(f"Error in test_put_in_use_api: {e}")

# Run the test functions
test_user_api()
# test_channel_api()
# test_put_in_use_api()
