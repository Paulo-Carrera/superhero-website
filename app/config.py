import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'loki445'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:P%40ulo445@localhost:5432/superhero_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPERHERO_API_URL = os.environ.get('SUPERHERO_API_URL')
    SUPERHERO_API_ACCESS_TOKEN = os.environ.get('SUPERHERO_API_ACCESS_TOKEN')




