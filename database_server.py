from flask import Flask, request, jsonify, send_file
import json
import os
import time
import rsa
import base64

app = Flask(__name__)

# Database class to handle JSON operations
class UserDatabase:
    _file_path = 'users.json'

    @classmethod
    def load_users(cls):
        """
        Load user credentials from the JSON file and return as a dictionary.
        """
        if os.path.exists(cls._file_path):
            with open(cls._file_path, 'r') as file:
                return json.load(file)
        else:
            return {}

    @classmethod
    def save_users(cls, user_data):
        """
        Save user credentials to the JSON file.
        """
        with open(cls._file_path, 'w') as file:
            json.dump(user_data, file, indent=4)

    @classmethod
    def add_user(cls, username, password, auth_method, telephone_number):
        """
        Add a new user with the provided details, and save to the database.
        """
        users = cls.load_users()

        # Check if the username already exists
        if username in users:
            return False, "Username already taken."

        # Add the new user
        users[username] = {
            "password": password,
            "auth_method": auth_method,
            "chat_id": None,  # chat_id will be added later via bot
            "telephone_number": telephone_number
        }

        # Save the updated users back to the file
        cls.save_users(users)
        return True, "User added successfully."

    @classmethod
    def add_chat_id(cls, username, chat_id):
        """
        Add or update the chat_id for an existing user.
        """
        users = cls.load_users()

        # Check if the user exists
        if username in users:
            users[username]['chat_id'] = chat_id
            cls.save_users(users)
            return True, "Chat ID added successfully."
        else:
            return False, "User not found."

    @classmethod
    def get_user(cls, username):
        """
        Get user details by username.
        """
        users = cls.load_users()
        return users.get(username)


# Authenticator class to handle authentication logic
class UserAuthenticator:
    @classmethod
    def check(cls, username, password):
        """
        Validate the username and password against the stored credentials.
        """
        user_data = UserDatabase.get_user(username)
        if user_data is not None and user_data['password'] == password:
            return True
        return False


private_key = None
public_key = None

def generate_new_key():
    global private_key, public_key
    # Flask routes
    # Generate RSA key pair (this could be stored securely)
    # Generate RSA key pair (this could be stored securely)
    (public_key, private_key) = rsa.newkeys(2048)
    print(f"Public key generated: {public_key}")
    print(f"Private key generated: {private_key}")

generate_new_key()
TIMETOCHANGEKEY = 600
TIMEENCRYPT = time.time()

@app.route('/get_public_key', methods=['GET'])
def get_public_key():
    # Return the public key to the client in PEM format
    return jsonify({"public_key": public_key.save_pkcs1().decode()})


def decrypt_json(data):
    print("----------Decrypting Incoming Message----------")
    global private_key
    try:
        encrypted_message = data.get('encrypted_message')
        if not encrypted_message:
            raise ValueError("No encrypted_message found in the request")

        print("The encrypted data: " + encrypted_message)
        # Decrypt the encrypted message using the private key
        encrypted_message_bytes = base64.b64decode(encrypted_message)
        print("\n decoded with private key")
        print(private_key)
        print("\n")
        decrypted_message = rsa.decrypt(encrypted_message_bytes, private_key)
        # Decode the byte message to string and then parse JSON
        json_data = json.loads(decrypted_message.decode())
        print("\ndecrypted data:")
        print(json_data)
        print("---------------Decryption Done---------------")
        return json_data
    except Exception as e:
        print(f"Error during decryption: {e}")
        raise


@app.route('/register', methods=['POST'])
def register():
    data = decrypt_json(request.json)
    username = data.get('username')
    password = data.get('password')
    auth_method = data.get('auth_method')
    telephone_number = data.get('telephone')

    print([username, password, auth_method, telephone_number])

    if not all([username, password, auth_method, telephone_number]):
        return jsonify({"error": "All fields (username, password, auth_method, telephone_number) are required"}), 400

    success, message = UserDatabase.add_user(username, password, auth_method, telephone_number)
    if success:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 401


@app.route('/login', methods=['POST'])
def login():
    try:
        data = decrypt_json(request.json)
        username = data.get('username')
        password = data.get('password')
        print(f"Login attempt: Username={username}, Password={password}")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if UserAuthenticator.check(username, password):
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Decryption failed or internal server error"}), 500


@app.route('/get_chat_id', methods=['POST'])
def get_chat_id():
    try:
        data = decrypt_json(request.json)
        username = data.get('username')
        password = data.get('password')
        print(f"Get Chat ID attempt: Username={username}, Password={password}")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if UserAuthenticator.check(username, password):
            user_data = UserDatabase.get_user(username)
            if user_data['chat_id']:
                return jsonify({"message": "Login successful", "chat_id": user_data['chat_id']}), 200
            else:
                return jsonify({"message": "Login successful", "telephone_number": user_data['telephone_number']}), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        print(f"Error fetching chat ID: {e}")
        return jsonify({"error": "Decryption failed or internal server error"}), 500


@app.route('/add_chat_id', methods=['POST'])
def add_chat_id():
    data = decrypt_json(request.json)
    username = data.get('username')
    chat_id = data.get('chat_id')

    if not username or not chat_id:
        return jsonify({"error": "Username and chat_id are required"}), 400

    success, message = UserDatabase.add_chat_id(username, chat_id)
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 404

@app.route('/get_fullness_txt', methods=['GET'])
def get_fullness_txt():
    file_path = './fullness.txt'  # Ensure this is the correct path to your file
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    
    
@app.route('/get_analysis', methods=['GET'])
def get_analysis():
    file_path = os.path.join(os.getcwd(), 'analysis.txt')
    print(file_path)
    # file_path = './analysis.txt'  # Ensure this is the correct path to your file
    try:
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


# Route to get the PNG image (storagetank_fullness.png)
@app.route('/get_fullness_image', methods=['GET'])
def get_fullness_image():
    file_path = './storagetank_fullness.png'  # Ensure this is the correct path to your PNG file
    try:
        return send_file(file_path, mimetype='image/png', as_attachment=True)
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route('/test', methods=['GET'])
def test_route():
    return "Server is running!"



@app.route('/who_is_in', methods=['POST', 'GET'])
def who_is_in():
    occupants_file = 'occupants.json'

    if request.method == 'POST':
        data = decrypt_json(request.json)  # Decrypt incoming encrypted data
        occupants = data.get('occupants')  # Extract "occupants" field

        # Check if occupants is empty or missing
        if not occupants:
            occupants = ["No one is in the factory"]

        # Load the current occupants list (if it exists) or initialize an empty one
        if os.path.exists(occupants_file):
            with open(occupants_file, 'r') as file:
                current_occupants = json.load(file)
        else:
            current_occupants = []

        # Append new occupants to the existing list, avoiding duplicates
        for occupant in occupants:
            if occupant not in current_occupants:
                current_occupants.append(occupant)

        # Save the updated occupants list to a JSON file
        with open(occupants_file, 'w') as file:
            json.dump(current_occupants, file, indent=4)

        return jsonify({"message": "Occupants list updated successfully", "occupants": current_occupants}), 200
    
    elif request.method == 'GET':
        # Load the current occupants list (if it exists) or initialize an empty one
        if os.path.exists(occupants_file):
            with open(occupants_file, 'r') as file:
                current_occupants = json.load(file)
        else:
            current_occupants = []

        # If the current occupants list is empty, update the message
        if not current_occupants:
            current_occupants = ["No one is in the factory"]

        return jsonify({"occupants": current_occupants}), 200


@app.route('/get_all_chat_ids', methods=['GET'])
def get_all_chat_ids():
    """
    Return all chat IDs of registered users.
    """
    users = UserDatabase.load_users()
    chat_ids = {user['chat_id'] for user in users.values() if user['chat_id']}
    
    return jsonify({'chat_ids': list(chat_ids)}), 200

if __name__ == '__main__':
    # Initialize an empty JSON file if it doesn't exist
    if not os.path.exists('users.json'):
        with open('users.json', 'w') as file:
            json.dump({}, file)

    app.run(host='0.0.0.0', port=5000, debug=True)
