from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS
from bson.json_util import dumps
import random
from datetime import datetime
from bson.objectid import ObjectId

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient('mongodb+srv://sahil:sahil123@cluster0.jcct62j.mongodb.net/?retryWrites=true&w=majority&appName'
                     '=Cluster0')
db = client['tip']
collection = db['quiz']
collection_users = db['Students']
questions = db['Questions']
score_collection = db['Score']


# Routes
@app.route('/api/login', methods=['POST'])
def login():
    # Assuming you receive email and password in the request
    email = request.json.get('email')
    password = request.json.get('password')
    print('%%%%%%%%%%%', email, password)

    # Query the database for the user with the provided email and password
    user = collection.find_one({'email': email, 'password': password})
    print('************', user)
    # If user exists, return a success response
    if user:
        user['_id'] = str(user['_id'])
        return jsonify({'message': 'Login successful', 'user': user}), 200
    else:
        return jsonify({'message': 'Invalid credentials'}), 401


@app.route('/api/data', methods=['POST'])
def add_data():
    new_data = request.get_json()
    print("*********************", new_data)

    required_fields = ['firstName', 'lastName', 'email']

    # Check if any of the required fields are missing or empty
    missing_fields = [field for field in required_fields if not new_data.get(field)]

    if missing_fields:
        return jsonify({'error': f'Missing or empty field: {", ".join(missing_fields)}'}), 400

    collection.insert_one(new_data)
    return jsonify({'message': 'Data added successfully!'}), 201


@app.route('/api/add/users', methods=['POST'])
def create_user():
    user_data = request.get_json()
    if 'email' in user_data and 'name' in user_data:
        inserted_user = collection.insert_one(user_data)
        return jsonify({'message': 'User created successfully!'}), 201
    else:
        return jsonify({'error': 'Email and password are required!'}), 400


@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = collection_users.find_one({'_id': user_id})
    if user:
        user['_id'] = str(user['_id'])
        return jsonify(user), 200
    else:
        return jsonify({'message': 'User not found'}), 404


@app.route('/api/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        user_id = ObjectId(user_id)
    except Exception as e:
        return jsonify({'error': 'Invalid user ID'}), 400

    updated_data = request.get_json()

    if not updated_data:
        return jsonify({'error': 'No data provided for update'}), 400

    # Remove the _id field from the updated data if it exists
    updated_data.pop('_id', None)

    result = collection.update_one({'_id': user_id}, {'$set': updated_data})

    if result.matched_count == 0:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'message': 'User updated successfully!'}), 200


@app.route('/api/delete/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        # Convert the user_id to ObjectId
        user_id = ObjectId(user_id)
    except Exception as e:
        return jsonify({'message': 'Invalid user ID'}), 400

    result = collection.delete_one({'_id': user_id})
    if result.deleted_count == 1:
        return jsonify({'message': 'User deleted successfully!'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404


@app.route('/api/users', methods=['GET'])
def get_all_users():
    users = collection.find()  # Retrieve all documents from the 'users' collection
    serialized_users = dumps(users)  # Serialize MongoDB documents to JSON
    return serialized_users, 200


@app.route('/get/questions', methods=['GET'])
def get_questions():
    # Get all questions from the database
    all_questions = list(questions.find())

    # Shuffle the list of questions
    random.shuffle(all_questions)

    # Select the first 5 questions
    selected_questions = all_questions[:5]

    # Serialize selected questions
    serialized_questions = dumps(selected_questions)

    return serialized_questions, 200


@app.route('/add/questions', methods=['POST'])
def add_question():
    new_question = request.json
    if 'question' not in new_question or 'options' not in new_question or 'answer' not in new_question:
        return jsonify({'error': 'Missing required fields'}), 400

    questions.insert_one(new_question)
    return jsonify({'message': 'Question added successfully'}), 201


@app.route('/questions', methods=['GET'])
def get_all_questions():
    all_questions = list(questions.find({}))
    serialized_users = dumps(all_questions)  # Serialize MongoDB documents to JSON
    return serialized_users, 200
    # Exclude _id field from the response


@app.route('/questions/<question_id>', methods=['DELETE'])
def delete_question(question_id):
    try:
        # Convert the user_id to ObjectId
        question_id = ObjectId(question_id)
    except Exception as e:
        return jsonify({'message': 'Invalid user ID'}), 400
    if not questions.find_one({'_id': question_id}):
        return jsonify({'error': 'Question not found'}), 404

    questions.delete_one({'_id': question_id})
    return jsonify({'message': 'Question deleted successfully'}), 200


@app.route('/submit/quiz', methods=['POST'])
def submit_quiz():
    data = request.get_json()
    user_id = data.get('id')
    score = data.get('score')

    # Get current date and time
    current_time = datetime.now()

    # Store the score along with current time in MongoDB
    score_collection.insert_one({'userId': user_id, 'score': score, 'timestamp': current_time})

    return jsonify({'success': True})


@app.route('/scores/<userId>', methods=['GET'])
def get_scores(userId):
    scores = list(score_collection.find({'userId': userId}))
    serialized_score = dumps(scores)
    return serialized_score, 200


if __name__ == '__main__':
    app.run(debug=True)
