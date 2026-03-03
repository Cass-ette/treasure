import json
from app.extensions import db
from datetime import datetime


class ChatConversation(db.Model):
    __tablename__ = 'chat_conversation'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False, default='新对话')
    model = db.Column(db.String(50), default='deepseek')
    messages = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_messages(self):
        try:
            return json.loads(self.messages)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_messages(self, msgs):
        self.messages = json.dumps(msgs, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'model': self.model,
            'messages': self.get_messages(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M'),
        }
