#!flask/bin/python
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from hashlib import md5


app = Flask(__name__, static_url_path = "")
auth = HTTPBasicAuth()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class Note(db.Model):
    '''Модель записи. Связана с БД'''
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        return '<Note %r>' % self.text

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    def make_public_note(self):
        return {"text":self.text, "url":url_for('get_note', note_id=self.id, _external=True)}

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


@app.route('/notebook/api/notes', methods = ['GET'])
@auth.login_required
def get_notes():
    return jsonify( { 'notes': [i.make_public_note() for i in Note.query.all()] } )

@app.route('/notebook/api/notes/<int:note_id>', methods = ['GET'])
@auth.login_required
def get_note(note_id):
    note = Note.query.get(note_id)
    if note:
        return jsonify( { 'note': note.make_public_note() } )
    abort(404)

@app.route('/notebook/api/notes', methods = ['POST'])
@auth.login_required
def create_note():
    if not request.json or not 'text' in request.json:
        abort(400)
    note = Note(text=request.json['text'])

    note.save()
    return jsonify( { 'note': note.make_public_note() } ), 201

@app.route('/notebook/api/notes/<int:note_id>', methods = ['PUT'])
@auth.login_required
def update_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        abort(404)
    if not (request.json and 'text' in request.json):
        abort(400)
    note.text = request.json.get('text', note.text)
    note.save()
    return jsonify( { 'note': note.make_public_note() } )
    
@app.route('/notebook/api/notes/<int:note_id>', methods = ['DELETE'])
@auth.login_required
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        abort(404)
    note.delete()
    return jsonify( { 'result': True } )
    
if __name__ == '__main__':
    db.create_all()
    app.run(debug = True)