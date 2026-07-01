import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
}

DB_NAME = "tourist_guide"

cities_table = """
CREATE TABLE IF NOT EXISTS cities (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    subtitle TEXT,
    description TEXT,
    image VARCHAR(500),
    map_url VARCHAR(500),
    accent VARCHAR(50),
    population VARCHAR(100),
    language VARCHAR(100),
    currency VARCHAR(50),
    climate VARCHAR(100),
    lat FLOAT,
    lng FLOAT,
    restaurants JSON,
    hotels JSON,
    transports JSON,
    places JSON
)
"""

users_table = """
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    country VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    birthdate VARCHAR(20),
    password VARCHAR(200) NOT NULL,
    created_at VARCHAR(50)
)
"""

reservations_table = """
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200),
    email VARCHAR(200),
    phone VARCHAR(50),
    birthdate VARCHAR(20),
    city_id VARCHAR(50),
    city_name VARCHAR(200),
    category VARCHAR(50),
    item_name VARCHAR(200),
    date_res VARCHAR(20),
    nights VARCHAR(20),
    persons VARCHAR(20),
    total VARCHAR(20),
    menu_items JSON,
    created_at VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending'
)
"""

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4")
cursor.execute(f"USE {DB_NAME}")
cursor.execute(cities_table)
cursor.execute(users_table)
cursor.execute(reservations_table)
conn.commit()
cursor.close()
conn.close()
print("Database and tables created successfully.")
