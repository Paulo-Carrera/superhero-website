import unittest
from app.app import create_app, db
from app.models import User
from flask import json
from flask_login import login_user, logout_user

class FlaskAppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test client and database."""
        cls.app = create_app()  
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False  
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Drop the test database."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        """Set up test data."""
        # Ensure clean state
        db.session.remove()
        db.drop_all()
        db.create_all()

        # Create and add a test user
        self.user = User(username='testuser', email='testuser@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()
        
        # Log in the test user
        self.client.post('/login', data=dict(email='testuser@example.com', password='password'), follow_redirects=True)

    def tearDown(self):
        """Clean up after each test."""
        db.session.remove()
        db.drop_all()
        db.create_all()

    def test_home_page(self):
        """Test the home page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('Redirecting', response.get_data(as_text=True))

    def test_login_page(self):
        """Test the login page."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Login', response.get_data(as_text=True))

    def test_signup_page(self):
        """Test the signup page."""
        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Sign Up', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()






