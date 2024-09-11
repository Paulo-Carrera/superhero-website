from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, Blueprint
from app.extensions import db, bcrypt, login_manager, migrate
from app.forms import LoginForm, SignupForm, CompareForm, SearchForm, EditProfileForm
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Character, UserFavorites
from app.utils import fetch_and_save_character, fetch_superhero_data, get_hero_comparison, get_superhero_data_from_db, save_character_to_db
import requests
import logging
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()
app = Flask(__name__)

# Initialize Blueprint
bp = Blueprint('app', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize extensions
def create_app():
    app = Flask(__name__)
    app.config.from_object('app.config.Config')

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Set up the user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @bp.route('/')
    def home():
        if not current_user.is_authenticated:
            return redirect(url_for('app.login'))

        favorite_characters = UserFavorites.query.filter_by(user_id=current_user.id).all()
        favorite_characters = [favorite.character for favorite in favorite_characters] if favorite_characters else []

        return render_template('home.html', favorite_characters=favorite_characters)

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('app.home'))
            else:
                app.logger.warning(f'Login failed for username: {form.username.data}')
                flash('Login failed. Check your username and/or password.', 'danger')
        return render_template('login.html', form=form)

    @bp.route('/signup', methods=['GET', 'POST'])
    def signup():
        form = SignupForm()
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            new_user = User(email=form.email.data, password_hash=hashed_password, username=form.username.data, profile_image=form.profile_image.data)
            db.session.add(new_user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('app.login'))
        return render_template('signup.html', form=form)

    @bp.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'success')
        return redirect(url_for('app.home'))

    @bp.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        profile = User.query.filter_by(email=current_user.email).first()
        return render_template('profile.html', profile=profile)
    
    @bp.route('/edit_profile', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        """Edit user profile if logged in."""
        form = EditProfileForm(obj=current_user)
        if form.validate_on_submit():
            current_user.username = form.username.data
            current_user.email = form.email.data
            current_user.profile_image = form.profile_image.data
            db.session.commit()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('app.profile'))
        return render_template('edit_profile.html', form=form)   

    @bp.route('/delete_profile', methods=['POST'])
    @login_required
    def delete_profile():
        """Delete user profile if logged in."""
        db.session.delete(current_user)
        db.session.commit()
        flash('Your profile has been deleted!', 'success')
        return redirect(url_for('app.home'))

    @bp.route('/search', methods=['GET', 'POST'])
    @login_required
    def search():
        form = SearchForm()
        results = []
        if form.validate_on_submit():
            character_name = form.name.data
            app.logger.debug(f'Search requested for character: {character_name}')
            existing_characters = Character.query.filter(Character.name.ilike(f'%{character_name}%')).all()
            if existing_characters:
                results = [char.to_dict() for char in existing_characters]
                app.logger.debug(f'Characters found in database: {results}')
                return render_template('search_results.html', form=form, results=results)
            else:
                api_results = fetch_superhero_data(character_name)
                app.logger.debug(f'Fetched results from API: {api_results}')
                if api_results:
                    new_characters = []
                    for char in api_results:
                        app.logger.debug(f'Processing character from API: {char["name"]}')
                        if not Character.query.filter_by(name=char['name']).first():
                            image_url = char.get('image', '')
                            if image_url:
                                app.logger.debug(f'Image URL for {char["name"]}: {image_url}')
                            else:
                                app.logger.debug(f'No image URL found for {char["name"]}')
                            new_character = Character(
                                api_id=char['id'],
                                name=char['name'],
                                powerstats=char['powerstats'],
                                biography=char['biography'],
                                appearance=char['appearance'],
                                work=char['work'],
                                connections=char['connections'],
                                image=image_url
                            )
                            db.session.add(new_character)
                            new_characters.append(new_character)
                            app.logger.debug(f'Added new character to database: {char["name"]}')
                    if new_characters:
                        db.session.commit()
                        app.logger.debug(f'New characters committed to the database.')
                        results = [char.to_dict() for char in new_characters]
                    else:
                        app.logger.debug(f'Characters already exist in the database.')
                    return render_template('search_results.html', form=form, results=results)
                else:
                    app.logger.debug(f'No results found in API response for character: {character_name}')
                    flash(f"No results found for {character_name}.", 'danger')
                    return redirect(url_for('app.search'))
        return render_template('search.html', form=form)

    @bp.route('/api/suggestions')
    def suggestions():
        query = request.args.get('query', '')
        if not query:
            return jsonify([])
        results = Character.query.filter(Character.name.ilike(f'%{query}%')).all()
        suggestions = [{'name': result.name} for result in results]
        print(f"Suggestions for query '{query}': {suggestions}")
        return jsonify(suggestions)

    @bp.route('/favorites', methods=['GET'])
    @login_required
    def favorites():
        """Show user's favorite characters."""
        if not current_user.is_authenticated:
            return redirect(url_for('app.login'))
        alignments = request.args.getlist('alignment')
        query = UserFavorites.query.join(Character, UserFavorites.character_id == Character.api_id)
        if alignments:
            query = query.filter(Character.biography['alignment'].astext.in_(alignments))
        favorites = query.all()
        for favorite in favorites:
            if isinstance(favorite.character.image, str):
                try:
                    image_data = json.loads(favorite.character.image)
                    if isinstance(image_data, dict) and 'url' in image_data:
                        favorite.character.image = image_data['url']
                except json.JSONDecodeError:
                    pass
        for favorite in favorites:
            print(f"Character ID {favorite.character.api_id} has image URL: {favorite.character.image}")
        return render_template('favorites.html', favorites=favorites)

    @bp.route('/add_favorite/<int:character_id>', methods=['POST'])
    @login_required
    def add_favorite(character_id):
        # Fetch and save the character from the API if necessary
        character = fetch_and_save_character(character_id)

        if character:
            # Check if the character is already in the user's favorites
            existing_favorite = UserFavorites.query.filter_by(user_id=current_user.id, character_id=character_id).first()

            if not existing_favorite:
                # Extract the character's image URL (ensure the structure is consistent)
                image_url = character.get('image', {}).get('url', 'No image URL')

                # Add a new favorite to the database
                new_favorite = UserFavorites(
                    user_id=current_user.id,
                    character_id=character_id,  # This should be the ID of the character
                    image=image_url
                )

                db.session.add(new_favorite)
                db.session.commit()
                flash(f'Character added to favorites!', 'success')
            else:
                flash('Character is already in your favorites.', 'info')
        else:
            flash('Character not found in the API or database.', 'danger')

        return redirect(url_for('app.favorites'))

    @bp.route('/remove_favorite/<int:character_id>', methods=['POST'])
    @login_required
    def remove_favorite(character_id):
        favorite = UserFavorites.query.filter_by(user_id=current_user.id, character_id=character_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            flash('Character removed from favorites!', 'success')
        else:
            flash('Character not found in favorites.', 'danger')
        return redirect(url_for('app.favorites'))

    @bp.route('/compare', methods=['GET', 'POST'])
    @login_required
    def compare():
        form = CompareForm()

        if form.validate_on_submit():
            hero1_name = form.hero1.data
            hero2_name = form.hero2.data

            # Redirect to results page with hero names
            return redirect(url_for('app.compare_results', hero1=hero1_name, hero2=hero2_name))

        # Render the comparison form page
        return render_template('compare.html', form=form)

    @bp.route('/compare_results')
    @login_required
    def compare_results():
        hero1_name = request.args.get('hero1')
        hero2_name = request.args.get('hero2')

        if not hero1_name or not hero2_name:
            return redirect(url_for('main.index'))

        # Fetch data from the database
        hero1_data = get_superhero_data_from_db(hero1_name)
        hero2_data = get_superhero_data_from_db(hero2_name)

        # If data is not found in the database, fetch from the API
        if not hero1_data:
            hero1_data = fetch_superhero_data(hero1_name)
            if hero1_data:
                save_character_to_db(hero1_data)

        if not hero2_data:
            hero2_data = fetch_superhero_data(hero2_name)
            if hero2_data:
                save_character_to_db(hero2_data)

        # Perform the comparison
        comparison = get_hero_comparison(hero1_data, hero2_data)

        if not comparison:
            return render_template('error.html', message="Error creating comparison.")

        return render_template('compare_results.html', comparison=comparison)


    @bp.route('/api/compare', methods=['POST'])
    @login_required
    def api_compare():
        data = request.json
        hero1 = data.get('hero1')
        hero2 = data.get('hero2')
        if hero1 and hero2:
            hero1_data = fetch_superhero_data(hero1)
            hero2_data = fetch_superhero_data(hero2)
            if hero1_data and hero2_data:
                comparison_data = get_hero_comparison(hero1_data, hero2_data)
                if comparison_data:
                    return jsonify(comparison_data)
                else:
                    return jsonify({'error': 'Comparison data not available.'}), 404
            else:
                return jsonify({'error': 'Failed to fetch superhero data.'}), 404
        return jsonify({'error': 'Invalid request.'}), 400

    app.register_blueprint(bp)

    return app




