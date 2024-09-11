DROP DATABASE IF EXISTS superhero_db;

CREATE DATABASE superhero_db;

\c superhero_db;

CREATE TABLE users(
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    profile_image VARCHAR(255)
);

CREATE TABLE characters(
    api_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    powerstats JSON,
    biography JSON,
    appearance JSON,
    work JSON,
    connections JSON,
    image JSON
);

CREATE TABLE user_favorites(
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    character_id INTEGER REFERENCES characters(api_id) ON DELETE CASCADE,
    image VARCHAR(255),
    CONSTRAINT unique_favorite UNIQUE (user_id, character_id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_characters_name ON characters(name);