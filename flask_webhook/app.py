from flask import Flask, request, jsonify
from pymongo import MongoClient
import datetime

app = Flask(__name__)

# Configure MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client.github_events

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    event = request.headers.get('X-GitHub-Event')

    if event == "push":
        handle_push_event(data)
    elif event == "pull_request":
        if data['action'] == 'opened':
            handle_pull_request_event(data)
        elif data['action'] == 'closed' and data['pull_request']['merged']:
            handle_merge_event(data)

    return "Event received", 200

def handle_push_event(data):
    event_data = {
        "request_id": data['head_commit']['id'],
        "author": data['pusher']['name'],
        "action": "PUSH",
        "from_branch": None,
        "to_branch": data['ref'].split('/')[-1],
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    db.events.insert_one(event_data)

def handle_pull_request_event(data):
    event_data = {
        "request_id": str(data['pull_request']['id']),
        "author": data['pull_request']['user']['login'],
        "action": "PULL REQUEST",
        "from_branch": data['pull_request']['head']['ref'],
        "to_branch": data['pull_request']['base']['ref'],
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    db.events.insert_one(event_data)

def handle_merge_event(data):
    event_data = {
        "request_id": str(data['pull_request']['id']),
        "author": data['pull_request']['user']['login'],
        "action": "MERGE",
        "from_branch": data['pull_request']['head']['ref'],
        "to_branch": data['pull_request']['base']['ref'],
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    db.events.insert_one(event_data)

@app.route('/events', methods=['GET'])
def get_events():
    events = list(db.events.find().sort("timestamp", -1).limit(10))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify(events)

if __name__ == '__main__':
    app.run(port=5000)
