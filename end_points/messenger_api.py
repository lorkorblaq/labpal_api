from flask import Flask, jsonify, request, abort
from flask_restful import Api, Resource, reqparse
from bson import ObjectId
from datetime import datetime, timedelta
from engine import db_clinical

POT_COLLECTION = db_clinical['pots']
USERS_COLLECTION = db_clinical['users']
CONVERSATION_COLLECTION = db_clinical['conversations']
MESSAGING_COLLECTION = db_clinical['messaging']


app = Flask(__name__)
api = Api(app)


# Store room information
rooms = {}
messenger_parser = reqparse.RequestParser()
# messenger_parser.add_argument('user', type=str, required=True, help='user is required')
# messenger_parser.add_argument('recipient', type=str, required=True, help='Recipient is required')
messenger_parser.add_argument('message', type=str, required=False, help='Message is required')
messenger_parser.add_argument('pot_name', type=str, required=False, help='Pot name is required')
messenger_parser.add_argument('description', type=str, required=False)

class CreatePot(Resource):
    def post(self, user_id):
        try:
            args = messenger_parser.parse_args()
            pot_name = args['pot_name']
            description = args['description']
            
            # Get user_id from request headers or authentication token
            
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            pot = POT_COLLECTION.find_one({'pot_name': pot_name})
            if user is None:
                return {"message": "User does not exist"}, 404
            if pot is not None:
                return {"message": "Pot already exists"}, 400
            # Insert pot document into the POT_COLLECTION
            pot_doc = {
                'pot_name': pot_name,
                'admin': user_id,  # The user who created the pot is the admin
                'members': [user_id],
                'description': description,
                'created_at': datetime.now()
            }
            POT_COLLECTION.insert_one(pot_doc)     
            return {'message': 'Pot created successfully'}, 201  # Use 201 status code for resource creation
        except Exception as e:
            return {'error': str(e)}, 500  # Internal Server Error for MongoDB-related errors

class GetPot(Resource):      
    def get(self):
        results = list(POT_COLLECTION.find())
        if not results:
            abort(404, message="No pots found")
        
        # Get the keys of the first document (assuming all documents have the same keys)
        keys = results[0].keys() if results else []

        # Iterate over the results and construct the response dynamically
        pot_list = []
        for result in results:
            pot_data = {}
            for key in keys:
                value = result[key]
                # Convert ObjectId to string
                if isinstance(value, ObjectId):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                pot_data[key] = value
                pot_list.append(pot_data)
        
        response = {"pots": pot_list}
        return response, 200
    


class JoinPot(Resource):
    def post(self, user_id, pot_id):
        try:
            args = messenger_parser.parse_args()
            pot_name = args['pot_name']
            
            # Check if the user exists
            user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
            if user is None:
                return {'error': 'User does not exist'}, 404
            
            # Get the user's full name
            username = user.get('firstname') + ' ' + user.get('lastname')
            
            # Check if the pot exists
            pot = POT_COLLECTION.find_one({'_id': ObjectId(pot_id)})
            pot_name = pot.get('pot_name')
            if pot is None:
                return {'error': f'{pot_name} does not exist'}, 404
            
            # Check if the user is already a member of the pot
            if user_id in pot.get('members', []):
                return {'message': f'{username} is already a member of the {pot_name} room'}, 200
            
            # Add the user to the pot
            POT_COLLECTION.update_one({'pot_name': pot_name}, {'$addToSet': {'members': user_id}})
            
            return {'message': f'{username} joined the {pot_name} room'}, 200
        except Exception as e:
            return {'error': str(e)}, 500  # Internal Server Error for MongoDB-related errors

class LeavePot(Resource):
    def post(self, user_id):
        args = messenger_parser.parse_args()
        pot_name = args['pot_name']
        pot = POT_COLLECTION.find_one({'pot_name': pot_name})
        user = USERS_COLLECTION.find_one({'_id': ObjectId(user_id)})
        username = user.get('firstname') + ' ' + user.get('lastname')
        if user is None:
            return {'error': 'User does not exist'}, 404
        if pot is None:
            return {'error': 'Pot name is required'}, 400
                # Check if the user is a member of the pot
        if user_id not in pot.get('members', []):
            return {'error': f'{username} is not in the pot'}, 400
        POT_COLLECTION.update_one({'pot_name': pot_name}, {'$pull': {'members': user_id}})
        return {'message': f'{username} left the pot'}, 200

class PrivateMessage(Resource):
    def post(self, sender_id, recipient_id):
        try:
            args = messenger_parser.parse_args()
            message_content = args['message']
            # Ensure sender and recipient exist
            sender = USERS_COLLECTION.find_one({'_id': ObjectId(sender_id)})
            recipient = USERS_COLLECTION.find_one({'_id': ObjectId(recipient_id)})
            if sender is None and recipient is None:
                return {'error': 'Sender and recipient does not exist'}, 404
            
            # Create conversation document if it doesn't exist
            conversation = CONVERSATION_COLLECTION.find_one({'participants': {'$all': [sender_id, recipient_id]}})
            if conversation is None:
                conversation_id = str(ObjectId())  # Generate unique conversation ID
                CONVERSATION_COLLECTION.insert_one({'_id': conversation_id, 'participants': [sender_id, recipient_id]})
            else:
                conversation_id = conversation['_id']
            
            # Store message in message collection
            message = {
                'conversation_id': conversation_id,
                'sender': sender_id,
                'recipient': recipient_id,
                'message': message_content,
                'timestamp': datetime.now()
            }
            MESSAGING_COLLECTION.insert_one(message)

            return {'message': 'Message sent successfully'}, 200
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    # def get(self, conversation_id):

class GlobalMessage(Resource):
    def post(self, sender_id, pot_id):
        try:
            args = messenger_parser.parse_args()
            sender_id = USERS_COLLECTION.find_one({'_id': ObjectId(sender_id)})
            sender = sender.get('firstname') + ' ' + sender.get('lastname')
            if sender is None:
                return {'message': 'User does not exist'}, 404
            pot_id = POT_COLLECTION.find_one({'_id': ObjectId(sender_id)})
            if pot_id is None:
                return {'message': 'Pot does not exist'}, 404
            message = args['message']
            # Get all members in the pot
            members = POT_COLLECTION.find_one({'_id': ObjectId(pot_id)}).get('members', [])
            if sender_id not in members:
                return {'error': f'{sender} is not a member of the pot'}, 400
            for member in members:
                if member != sender_id:
                    message_doc = {
                        'sender': sender_id,
                        'recipient': member,
                        'message': message,
                        'timestamp': datetime.now()
                    }
                    MESSAGING_COLLECTION.insert_one(message_doc)

            return {'message': 'Message sent successfully'}, 200
        except Exception as e:
            return {'error': str(e)}, 500
        
class PotMessage(Resource):
    def post(self, sender_id, pot_id):
        try:
            args = messenger_parser.parse_args()
            message = args['message']
            sender_id = USERS_COLLECTION.find_one({'_id': ObjectId(sender_id)})
            sender = sender.get('firstname') + ' ' + sender.get('lastname')
            if sender_id is None:
                return {'message': 'User does not exist'}, 404
            
            pot = POT_COLLECTION.find_one({'_id': ObjectId(pot_id)})
            if pot_id is None:
                return {'message': 'Pot does not exist'}, 404

            # Check if the sender is a member of the pot
            if sender_id not in pot.get('members', []):
                return {'error': 'Sender is not a member of the pot'}, 400
            
            # Construct the message document
            message_doc = {
                'sender': sender_id,
                'recipient': pot_id,  # Indicate that it's a group message to the pot
                'message': message,
                'timestamp': datetime.now()
            }
            
            # Insert the message into the messaging collection
            MESSAGING_COLLECTION.insert_one(message_doc)

            return {'message': 'Group message sent successfully'}, 200
        except Exception as e:
            return {'error': str(e)}, 500



if __name__ == '__main__':
    app.run(debug=True)
