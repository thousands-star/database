from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

class UserAuthenticator:
    _user_credentials = {}  # Class variable to hold user credentials
    
    @classmethod
    def load_users(cls, file_path='users.json'):
        """
        Load user credentials from the JSON file and store them in the class variable.
        """
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                cls._user_credentials = json.load(file)
        else:
            cls._user_credentials = {}
    
    @classmethod
    def save_users(cls, file_path='users.json'):
        """
        Save user credentials to the JSON file from the class variable.
        """
        with open(file_path, 'w') as file:
            json.dump(cls._user_credentials, file, indent=4)

    @classmethod
    def check(cls, username, password):
        """
        Validate the username and password against the stored credentials.
        """
        cls.load_users()

        user_data = cls._user_credentials.get(username)
        if user_data is not None and user_data['password'] == password:
            return True
        return False
    
    @classmethod
    def add_user(cls, username, password, auth_method, telephone_number, file_path='users.json'):
        """
        Add a new user with additional details (excluding chat_id) to the credentials JSON file and update the class variable.
        """
        # Ensure users are loaded
        cls.load_users(file_path)
        
        # Check if the username already exists
        if username in cls._user_credentials:
            return False, "Username already taken."

        # Add the new user with the fields except chat_id
        cls._user_credentials[username] = {
            "password": password,
            "auth_method": auth_method,
            "chat_id": None,  # chat_id will be updated later by the Telegram bot
            "telephone_number": telephone_number
        }

        # Save the new user to the file
        cls.save_users(file_path)
        return True, "User added successfully."
    
    @classmethod
    def add_chat_id(cls, username, chat_id, file_path='users.json'):
        """
        Update the user's chat_id for Telegram bot integration.
        """
        # Ensure users are loaded
        cls.load_users(file_path)
        
        # Check if the username exists
        if username not in cls._user_credentials:
            return False, "Username not found."

        # Update the chat_id for the user
        cls._user_credentials[username]['chat_id'] = chat_id

        # Save the updated user data
        cls.save_users(file_path)
        return True, "Chat ID added successfully."

# Flask routes

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    auth_method = data.get('auth_method')
    telephone_number = data.get('telephone_number')
    
    if not all([username, password, auth_method, telephone_number]):
        return jsonify({"error": "All fields (username, password, auth_method, telephone_number) are required"}), 400
    
    success, message = UserAuthenticator.add_user(username, password, auth_method, telephone_number)
    if success:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 400

@app.route('/add_chat_id', methods=['POST'])
def add_chat_id():
    """
    Endpoint for the Telegram bot to send the chat_id and link it to a user.
    """
    data = request.json
    username = data.get('username')
    chat_id = data.get('chat_id')

    if not all([username, chat_id]):
        return jsonify({"error": "Username and chat ID are required"}), 400

    success, message = UserAuthenticator.add_chat_id(username, chat_id)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    if UserAuthenticator.check(username, password):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


if __name__ == '__main__':
    # Initialize an empty JSON file if it doesn't exist
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as file:
            json.dump({}, file)

    app.run(debug=True)
