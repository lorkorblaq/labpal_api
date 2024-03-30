import unittest
from datetime import datetime
from api import app  # Import your Flask app and collections
print(app)
from api import CHANNELS_COLLECTION 
print(CHANNELS_COLLECTION) 

def format_datetime(datetime_str):
    parsed_datetime = datetime.fromisoformat(datetime_str)
    formatted_datetime = parsed_datetime.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_datetime

class TestChannelEndpoints(unittest.TestCase):

    def setUp(self):    
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        # Clear the test database after each test
        CHANNELS_COLLECTION.delete_many({})

    def test_channel_push(self):
        # Test the /api/channel/push/<string:user_id>/ endpoint
        payload = {
            "item": "test_item",
            "lot_numb": "123456",
            "direction": "test_direction",
            "location": "test_location",
            "quantity": 5,
            "description": "test_description"
        }
        print(payload)
        response = self.app.post('/api/channel/push/1', json=payload)
        data = response.get_json()

        self.assertEqual(response.status_code, 308)
        self.assertEqual(data['message'], 'Channel created successfully')

        # Check if the channel was inserted into the database
        channels = CHANNELS_COLLECTION.find({})
        self.assertEqual(channels.count(), 1)

        # Assert the values inserted into the database
        inserted_channel = channels[0]
        self.assertEqual(inserted_channel['item'], payload['item'])
        self.assertEqual(inserted_channel['lot_numb'], payload['lot_numb'])
        self.assertEqual(inserted_channel['direction'], payload['direction'])
        self.assertEqual(inserted_channel['location'], payload['location'])
        self.assertEqual(inserted_channel['quantity'], payload['quantity'])
        self.assertEqual(inserted_channel['description'], payload['description'])

    def test_channel_get_all(self):
        # Test the /api/channels/get/ endpoint
        # First, insert some test data into the database
        test_channels = [
            {"item": "test_item_1", "lot_numb": "123456", "direction": "test_direction_1", "location": "test_location_1", "quantity": 5, "description": "test_description_1"},
            {"item": "test_item_2", "lot_numb": "654321", "direction": "test_direction_2", "location": "test_location_2", "quantity": 10, "description": "test_description_2"}
        ]
        CHANNELS_COLLECTION.insert_many(test_channels)

        response = self.app.get('/api/channels/get/')
        data = response.get_json()

        self.assertEqual(response.status_code, 308)
        self.assertTrue('channels' in data)
        self.assertEqual(len(data['channels']), 2)  # Check if all test channels were returned
         # Check if the datetime format is correct for each channel
        for channel in data['channels']:
            self.assertTrue('created at' in channel)
            self.assertIsInstance(channel['created at'], str)  # Ensure it's a string
            self.assertEqual(format_datetime(channel['created at']), "2024-03-26 09:51:12")  # Adjust the expected format as needed


    # You can add more tests for other endpoints in a similar manner

if __name__ == '__main__':
    unittest.main()