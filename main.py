from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Use /tmp for SQLite storage in AppSail
db_path = os.path.join("/tmp", "db.sqlite")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# ------------------ MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(500), nullable=False)
    answers = db.relationship("Answer", backref="question", cascade="all, delete-orphan")

    def __init__(self, comment):
        self.comment = comment

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer = db.Column(db.String(500), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __init__(self, answer, question_id):
        self.answer = answer
        self.question_id = question_id

# ------------------ SCHEMAS ------------------
class AnswerSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    answer = fields.Str()
    question_id = fields.Int()

class UserSchema(ma.Schema):
    id = fields.Int(dump_only=True)
    comment = fields.Str()
    answers = fields.Nested(AnswerSchema, many=True)

    class Meta:
        fields = ("id", "comment", "answers")

user_schema = UserSchema()
users_schema = UserSchema(many=True)
answer_schema = AnswerSchema()
answers_schema = AnswerSchema(many=True)

# ------------------ ROUTES ------------------
@app.route('/add', methods=['POST'])
def add_comment():
    data = request.get_json()
    new_comment = User(data['comment'])
    db.session.add(new_comment)
    db.session.commit()
    return user_schema.jsonify(new_comment)

@app.route('/home', methods=['GET'])
def home():
    all_comments = User.query.all()
    return jsonify(users_schema.dump(all_comments))

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete_comment(id):
    comment = User.query.get(id)
    if not comment:
        return jsonify({'error': 'Question not found'}), 404
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'Question deleted successfully', 'id': id})

@app.route('/update/<int:id>', methods=['PATCH'])
def update_comment(id):
    comment = User.query.get(id)
    if not comment:
        return jsonify({'error': 'Question not found'}), 404
    data = request.get_json()
    if 'comment' in data:
        comment.comment = data['comment']
    db.session.commit()
    return user_schema.jsonify(comment)

@app.route('/add_answer/<int:question_id>', methods=['POST'])
def add_answer(question_id):
    question = User.query.get(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    data = request.get_json()
    new_answer = Answer(data['answer'], question_id)
    db.session.add(new_answer)
    db.session.commit()
    return answer_schema.jsonify(new_answer)

@app.route('/delete_answer/<int:id>', methods=['DELETE'])
def delete_answer(id):
    ans = Answer.query.get(id)
    if not ans:
        return jsonify({'error': 'Answer not found'}), 404
    db.session.delete(ans)
    db.session.commit()
    return jsonify({'message': 'Answer deleted successfully', 'id': id})

@app.route('/update_answer/<int:id>', methods=['PATCH'])
def update_answer(id):
    ans = Answer.query.get(id)
    if not ans:
        return jsonify({'error': 'Answer not found'}), 404
    data = request.get_json()
    if 'answer' in data:
        ans.answer = data['answer']
    db.session.commit()
    return answer_schema.jsonify(ans)

# ------------------ MAIN ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



