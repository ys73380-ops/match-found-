from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database files
MESSAGES_DB = 'dating_messages.json'

def load_database(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_database(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_messages(room_id, last_id=0):
    messages = load_database(MESSAGES_DB)
    room_messages = messages.get(room_id, [])
    # Filter messages newer than last_id
    filtered = [msg for msg in room_messages if msg['id'] > last_id]
    # Sort by id
    filtered.sort(key=lambda x: x['id'])
    return filtered

def add_message(room_id, sender_id, text):
    messages = load_database(MESSAGES_DB)
    if room_id not in messages:
        messages[room_id] = []
    
    # Get next message ID
    max_id = max([msg['id'] for msg in messages[room_id]], default=0)
    new_id = max_id + 1
    
    message = {
        'id': new_id,
        'sender_id': sender_id,
        'text': text,
        'created_at': datetime.now().isoformat()
    }
    
    messages[room_id].append(message)
    save_database(MESSAGES_DB, messages)
    return message

@app.route('/')
def index():
    return send_from_directory('.', 'chat.html')

@app.route('/api/messages', methods=['GET'])
def get_messages_api():
    room_id = request.args.get('room')
    last_id = int(request.args.get('last_id', 0))
    
    if not room_id:
        return jsonify({'success': False, 'error': 'Room ID required'}), 400
    
    messages = get_messages(room_id, last_id)
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/send', methods=['POST'])
def send_message_api():
    data = request.json
    room_id = data.get('room')
    sender_id = data.get('sender_id')
    text = data.get('text')
    
    if not all([room_id, sender_id, text]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    if not text.strip():
        return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
    
    # Check if room exists
    rooms = load_database('dating_rooms.json')
    if room_id not in rooms or not rooms[room_id].get('is_active'):
        return jsonify({'success': False, 'error': 'Invalid or inactive room'}), 400
    
    # Check if sender is part of the room
    room = rooms[room_id]
    if sender_id not in [room['user1_id'], room['user2_id']]:
        return jsonify({'success': False, 'error': 'Not authorized for this room'}), 403
    
    message = add_message(room_id, sender_id, text.strip())
    return jsonify({'success': True, 'message': message})

# Vercel handler
from vercel_wsgi import handle_wsgi_event

def handler(event, context):
    return handle_wsgi_event(app, event, context)
