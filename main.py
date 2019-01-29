#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask_httpauth import HTTPBasicAuth
from hashlib import md5


app = Flask(__name__, static_url_path = "")
auth = HTTPBasicAuth()


users = {
    "test": "23eeeb4347bdd26bfc6b7ee9a3b755dd",
}

def md5_verify(username, password):
    if username in users: 
        if users[username] == md5(str(password).encode('utf-8')).hexdigest():
            return True
    return False


@auth.verify_password
def verify_pw(username, password):
    return md5_verify(username, password)

@auth.hash_password
def hash_pw(password):
    return md5(password).hexdigest()

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

notes = [
    {
        'id': 1,
        'text': 'Buy groceries',
    },
    {
        'id': 2,
        'title': 'Learn Python',
    }
]
    
def make_public_note(note):
    note = dict((k, v) for k, v in note.items())
    note['url'] = url_for('get_note', note_id=note.pop('id'), _external=True)
    return note

@app.route('/notebook/api/notes', methods = ['GET'])
@auth.login_required
def get_notes():
    return jsonify( { 'notes': list(map(make_public_note, notes)) } )

@app.route('/notebook/api/notes/<int:note_id>', methods = ['GET'])
@auth.login_required
def get_note(note_id):
    note = list(filter(lambda t: t['id'] == note_id, notes))
    if note:
        return jsonify( { 'note': make_public_note(note[0]) } )
    abort(404)

@app.route('/notebook/api/notes', methods = ['POST'])
@auth.login_required
def create_note():
    if not request.json or not 'text' in request.json:
        abort(400)
    note = {
        'id': notes[-1]['id'] + 1,
        'text': request.json['text'],
    }
    notes.append(note)
    return jsonify( { 'note': make_public_note(note) } ), 201

@app.route('/notebook/api/notes/<int:note_id>', methods = ['PUT'])
@auth.login_required
def update_note(note_id):
    note = list(filter(lambda t: t['id'] == note_id, notes))
    if not note:
        abort(404)
    if not request.json:
        abort(400)
    if 'text' in request.json and type(request.json['text']) != unicode:
        abort(400)
    note[0]['text'] = request.json.get('text', note[0]['text'])
    return jsonify( { 'note': make_public_note(note[0]) } )
    
@app.route('/notebook/api/notes/<int:note_id>', methods = ['DELETE'])
@auth.login_required
def delete_note(note_id):
    note = list(filter(lambda t: t['id'] == note_id, notes))
    if len(note) == 0:
        abort(404)
    notes.remove(note[0])
    return jsonify( { 'result': True } )
    
if __name__ == '__main__':
    app.run(debug = True)