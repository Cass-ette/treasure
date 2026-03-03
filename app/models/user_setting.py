from app.extensions import db
from datetime import datetime


class UserSetting(db.Model):
    __tablename__ = 'user_setting'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'key', name='uq_user_setting'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_value(user_id, key, default=None):
        setting = UserSetting.query.filter_by(user_id=user_id, key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set_value(user_id, key, value):
        setting = UserSetting.query.filter_by(user_id=user_id, key=key).first()
        if setting:
            setting.value = value
        else:
            setting = UserSetting(user_id=user_id, key=key, value=value)
            db.session.add(setting)
        db.session.commit()
