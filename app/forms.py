from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo

class SearchForm(FlaskForm):
    name = StringField('Search for a Superhero!', validators=[DataRequired()])
    submit = SubmitField('Search')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    profile_image = StringField('Profile Image URL')
    submit = SubmitField('Register')

class CompareForm(FlaskForm):
    hero1 = StringField('First Superhero:', validators=[DataRequired()])
    hero2 = StringField('Second Superhero:', validators=[DataRequired()])
    submit = SubmitField('Compare')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    profile_image = StringField('Profile Image URL')
    submit = SubmitField('Update')



