from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db, bcrypt
from sqlalchemy.dialects.postgresql import JSON
import json

class User(db.Model, UserMixin):
    """Represents a user in the system."""

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_image = db.Column(db.String(255))

    # Relationship with UserFavorites
    favorites = db.relationship('UserFavorites', back_populates='user', cascade='all, delete-orphan', lazy=True)

    def set_password(self, password):
        """Set hashed password."""
        self.password_hash = generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if provided password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Character(db.Model):
    """Represents a superhero character."""

    __tablename__ = 'characters'
    api_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    powerstats = db.Column(JSON)
    biography = db.Column(JSON)
    appearance = db.Column(JSON)
    work = db.Column(JSON)
    connections = db.Column(JSON)
    image = db.Column(JSON, nullable=True)  # Updated to JSON for consistency

    # Relationship with UserFavorites
    favorited_by = db.relationship('UserFavorites', back_populates='character', lazy=True)

    def __repr__(self):
        return f'<Character {self.name}>'

    def to_dict(self):
        """Convert character to a dictionary."""
        image_url = None
        if isinstance(self.image, dict) and 'url' in self.image:
            image_url = self.image['url']
        
        return {
            'api_id': self.api_id,
            'name': self.name,
            'powerstats': self.powerstats,
            'biography': self.biography,
            'appearance': self.appearance,
            'work': self.work,
            'connections': self.connections,
            'image': image_url
        }

class UserFavorites(db.Model):
    """Represents a user's favorite character."""

    __tablename__ = 'user_favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('characters.api_id'), nullable=False)
    image = db.Column(db.String(255))

    # Relationships
    user = db.relationship('User', back_populates='favorites')
    character = db.relationship('Character', back_populates='favorited_by')

    __table_args__ = (db.UniqueConstraint('user_id', 'character_id', name='unique_favorite'),)

    def __repr__(self):
        return f'<UserFavorites user_id={self.user_id} character_id={self.character_id}>'
