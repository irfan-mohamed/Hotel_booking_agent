import jwt
import datetime
import hashlib
from app import db
    def generate_email_verification_token(self):
        payload = {
            'guest_id': self.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        # Ensure token is a string for hashing
        token_str = token if isinstance(token, str) else token.decode('utf-8')
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        self.email_verification_token = token_hash
        db.session.commit()
        return token_str
    @classmethod
    def find_by_verification_token(cls, token):
        # Ensure token is a string for hashing
        token_str = token if isinstance(token, str) else token.decode('utf-8')
        token_hash = hashlib.sha256(token_str.encode()).hexdigest()
        return cls.query.filter_by(email_verification_token=token_hash).first()