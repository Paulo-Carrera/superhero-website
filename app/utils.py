import requests
import os
from dotenv import load_dotenv
from app.models import db, Character
import json
import logging
from urllib.parse import urljoin
from app.config import Config

# Load environment variables
load_dotenv()

SUPERHERO_API_URL = os.getenv('SUPERHERO_API_URL')
SUPERHERO_API_ACCESS_TOKEN = os.getenv('SUPERHERO_API_ACCESS_TOKEN')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_hero_comparison(hero1_data, hero2_data):
    # If the data is empty or None, return None
    if not hero1_data or not hero2_data:
        return None

    # Check if hero1_data and hero2_data are lists, extract the first result if they are
    if isinstance(hero1_data, list):
        hero1_data = hero1_data[0] if len(hero1_data) > 0 else None
    if isinstance(hero2_data, list):
        hero2_data = hero2_data[0] if len(hero2_data) > 0 else None

    # Ensure that after extracting the first result, we still have valid data
    if not hero1_data or not hero2_data:
        return None

    # Ensure that hero1_data and hero2_data are dictionaries
    if not isinstance(hero1_data, dict) or not isinstance(hero2_data, dict):
        return None

    # Handle image URL extraction properly
    def get_image_url(data):
        image = data.get('image')
        if isinstance(image, dict):
            return image.get('url')
        return image

    # Create a comparison dictionary
    comparison = {
        'hero1': {
            'name': hero1_data.get('name'),
            'image_url': get_image_url(hero1_data),  
            'powerstats': hero1_data.get('powerstats'),
            'biography': hero1_data.get('biography'),
            'appearance': hero1_data.get('appearance'),
            'work': hero1_data.get('work'),
            'connections': hero1_data.get('connections'),
        },
        'hero2': {
            'name': hero2_data.get('name'),
            'image_url': get_image_url(hero2_data),  
            'powerstats': hero2_data.get('powerstats'),
            'biography': hero2_data.get('biography'),
            'appearance': hero2_data.get('appearance'),
            'work': hero2_data.get('work'),
            'connections': hero2_data.get('connections'),
        },
    }

    return comparison


def fetch_and_save_character(api_character_id):
    url = f"{SUPERHERO_API_URL}/{SUPERHERO_API_ACCESS_TOKEN}/{api_character_id}" 
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        if data.get('response') == 'success':
            char = data  # The API returns the character directly
            if not char:
                logger.warning(f"Character with ID {api_character_id} not found in API.")
                return None

            # Extract and log character data
            image_url = char.get('image', {}).get('url', 'No image URL')
            logger.debug(f"Fetched character: {char.get('name')}, Image URL: {image_url}")

            # Save or update character data in the database
            save_character_to_db(char)

            return char
        else:
            logger.error(f"API response error: {data.get('error')}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return None
    except ValueError as e:
        logger.error(f"JSON decoding error: {e}")
        return None

def fetch_superhero_data(character_name):
    api_url = f'{SUPERHERO_API_URL}{SUPERHERO_API_ACCESS_TOKEN}/search/{character_name}'
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()
    
        data = response.json()
        if data.get('response') == 'success':
            results = data.get('results', [])
            if results:
                return results  # Return a list of dictionaries
        else:
            logger.error(f"API response error: {data.get('error')}")
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception: {str(e)}")
        return []
    
    # If not found in the database, fetch from the API
    api_url = f'{SUPERHERO_API_URL}{SUPERHERO_API_ACCESS_TOKEN}/search/{character_name}'
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        if data.get('response') == 'success':
            results = data.get('results', [])
            if results:
                # Assuming the first result is the most relevant one
                superhero_data = results[0]
                # You might want to handle saving this data to your database here
                return {
                    'name': superhero_data.get('name'),
                    'image_url': superhero_data.get('image') and superhero_data['image'].get('url'),
                    'powerstats': superhero_data.get('powerstats', {}),
                    'biography': superhero_data.get('biography', {}),
                    'appearance': superhero_data.get('appearance', {}),
                    'work': superhero_data.get('work', {}),
                    'connections': superhero_data.get('connections', {}),
                }
            else:
                logger.error(f"No results found for character: {character_name}")
                return {}
        else:
            logger.error(f"API response error: {data.get('error')}")
            return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception: {str(e)}")
        return {}
    
def get_superhero_data_from_db(character_name):
    # Fetch the superhero from the database by name
    superhero = Character.query.filter_by(name=character_name).first()
    
    # Check if superhero was found
    if superhero:
        # Convert superhero to a dictionary and return
        return superhero.to_dict()
    else:
        # Return None if no superhero found
        return None

def fetch_suggestions(query):
    api_url = f"{SUPERHERO_API_URL}/search"
    params = {'query': query}
    headers = {
        'Authorization': f'Bearer {SUPERHERO_API_ACCESS_TOKEN}'
    }
    
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()  
        data = response.json()
        
        return [item['name'] for item in data.get('results', [])]
    except requests.RequestException as e:
        logger.error(f"An error occurred: {e}")
        return []

def search_superhero(query):
    """
    Search for superheroes in the database using case-insensitive matching (ILIKE).
    """
    try:
        # Perform a case-insensitive search using ILIKE in PostgreSQL
        results = Character.query.filter(Character.name.ilike(f'%{query}%')).all()
        return results
    except Exception as e:
        logger.error(f"An error occurred during the search: {e}")
        return []

def save_character_to_db(character_data):
    # Check if character_data is a dictionary
    if isinstance(character_data, dict):
        existing_character = Character.query.filter_by(name=character_data.get('name')).first()
        if not existing_character:
            new_character = Character(
                name=character_data.get('name'),
                image_url=character_data.get('image_url'),
                powerstats=character_data.get('powerstats'),
                biography=character_data.get('biography'),
                appearance=character_data.get('appearance'),
                work=character_data.get('work'),
                connections=character_data.get('connections'),
            )
            db.session.add(new_character)
            db.session.commit()



