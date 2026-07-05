import json
from datetime import datetime
import mysql.connector
from typing import Any, Dict, List, Optional

import config
from logger import get_logger

log = get_logger()


def _connect():
    try:
        return mysql.connector.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASS,
            database=config.MYSQL_DB,
        )
    except mysql.connector.Error as e:
        if e.errno == 1049:  # Unknown database
            # Try connecting without database to create it
            try:
                temp_conn = mysql.connector.connect(
                    host=config.MYSQL_HOST,
                    port=config.MYSQL_PORT,
                    user=config.MYSQL_USER,
                    password=config.MYSQL_PASS,
                )
                cursor = temp_conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{config.MYSQL_DB}`")
                temp_conn.commit()
                cursor.close()
                temp_conn.close()
                # Now connect with database
                return mysql.connector.connect(
                    host=config.MYSQL_HOST,
                    port=config.MYSQL_PORT,
                    user=config.MYSQL_USER,
                    password=config.MYSQL_PASS,
                    database=config.MYSQL_DB,
                )
            except mysql.connector.Error as e2:
                log.error(f"Failed to create database: {e2}")
                return None
        log.error(f"Connection error: {e}")
        return None


def init_tables():
    """Create tables if they don't exist"""
    conn = _connect()
    if not conn:
        return False
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                country VARCHAR(100),
                phone VARCHAR(50),
                birthdate DATE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Cities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cities (
                id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                subtitle TEXT,
                description TEXT,
                image VARCHAR(500),
                map_url VARCHAR(500),
                accent JSON,
                population VARCHAR(100),
                language VARCHAR(100),
                currency VARCHAR(10) DEFAULT 'MAD',
                climate VARCHAR(100),
                lat DECIMAL(10,8),
                lng DECIMAL(11,8),
                restaurants JSON,
                hotels JSON,
                transports JSON,
                places JSON
            )
        """)
        
        # Reservations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                phone VARCHAR(50),
                birthdate DATE,
                city_id VARCHAR(100),
                city_name VARCHAR(255),
                category VARCHAR(50),
                item_name VARCHAR(255),
                date_res DATE,
                nights INT,
                persons INT,
                total VARCHAR(50),
                menu_items JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'pending'
            )
        """)
        
        conn.commit()
        return True
    except mysql.connector.Error as e:
        log.error(f"init_tables error: {e}")
        return False
    finally:
        _close(cursor, conn)


def _default_cities():
    return [
        {
            "id": "casablanca", "name": "Casablanca", "subtitle": "Métropole Atlantique",
            "description": "Plus grande ville du Maroc, cœur économique du pays. La Mosquée Hassan II, chef-d'œuvre architectural, surplombe l'océan Atlantique. Le centre-ville Art déco, la Corniche et le Morocco Mall en font une destination vibrante.",
            "image": "assets/cities/casablanca.png", "map_url": "https://maps.app.goo.gl/V4vNisZuKP3tirTR8",
            "accent": [82, 116, 158],
            "stats": {"population": "3,7 millions", "language": "Arabe, Berbère, Français", "currency": "MAD", "climate": "Tempéré côtier"},
            "location": {"lat": 33.5731, "lng": -7.5898},
            "restaurants": [
                {"name": "Le Cabestan", "image": "assets/cities/cabestan.png", "note": "Cuisine marocaine traditionnelle.", "stars": 5},
                {"name": "Rick's Café", "image": "assets/cities/rickscafe.png", "note": "Ambiance inspirée du film Casablanca.", "stars": 4},
                {"name": "La Sqala", "image": "assets/cities/sqala.jpg", "note": "Cuisine marocaine raffinée.", "stars": 4},
            ],
            "hotels": [
                {"name": "Four Seasons Casablanca", "image": "assets/cities/four.png", "note": "Hôtel de luxe face à l'océan.", "stars": 5},
                {"name": "Hyatt Regency Casablanca", "image": "assets/cities/hyatt.png", "note": "Centre-ville moderne.", "stars": 5},
                {"name": "Sofitel Casablanca Tour Blanche", "image": "assets/cities/sofitel.jpg", "note": "Hôtel 5 étoiles spa.", "stars": 5},
            ],
            "transports": [
                {"name": "Train (ONCF)", "image": "assets/cities/rabat.png", "note": "ONCF"},
                {"name": "Tramway", "image": "assets/cities/rabat.png", "note": "T1, T2, T3, T4"},
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "Busway"},
            ],
            "places": [
                {"name": "Mosquée Hassan II", "image": "assets/cities/hassan2.jpg", "note": "Grande mosquée au bord de l'océan.", "stars": 5},
                {"name": "Corniche", "image": "assets/cities/cornich.jpg", "note": "Zone touristique animée.", "stars": 4},
                {"name": "Morocco Mall", "image": "assets/cities/mall.jpg", "note": "Plus grand mall d'Afrique.", "stars": 4},
            ],
        },
        {
            "id": "marrakech", "name": "Marrakech", "subtitle": "La Ville Rouge",
            "description": "Perle du sud marocain, célèbre pour sa médina animée, la place Jemaa el-Fna et ses palais somptueux. Entre traditions et modernité, Marrakech est une étape incontournable.",
            "image": "assets/cities/marrakech.png", "map_url": "https://maps.app.goo.gl/kUZYhmQy31P6KY2k6",
            "accent": [196, 78, 62],
            "stats": {"population": "1 million", "language": "Arabe, Berbère, Français, Anglais", "currency": "MAD", "climate": "Semi-aride chaud"},
            "location": {"lat": 31.6295, "lng": -7.9811},
            "restaurants": [
                {"name": "Al Fassia", "image": "assets/cities/alfna.jpg", "note": "Cuisine marocaine raffinée.", "stars": 5},
                {"name": "Le Jardin", "image": "assets/cities/lejardin.jpg", "note": "Terrasse avec vue imprenable.", "stars": 4},
                {"name": "Café de la Poste", "image": "assets/cities/bleu.jpg", "note": "Ambiance chic et décontractée.", "stars": 4},
            ],
            "hotels": [
                {"name": "La Mamounia", "image": "assets/cities/mamoniya.jpg", "note": "Palais légendaire au cœur des jardins.", "stars": 5},
                {"name": "Royal Mansour", "image": "assets/cities/royal.jpg", "note": "Hôtel traditionnel avec patio.", "stars": 5},
                {"name": "Riad Fès", "image": "assets/cities/riad.jpg", "note": "Riad authentique et luxueux.", "stars": 5},
            ],
            "transports": [
                {"name": "Train (ONCF)", "image": "assets/cities/rabat.png", "note": "ONCF"},
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "ALSA"},
                {"name": "Taxi", "image": "assets/cities/rabat.png", "note": "Petits et grands taxis"},
            ],
            "places": [
                {"name": "Jemaa el-Fna", "image": "assets/cities/jemaa.jpg", "note": "Place animée célèbre dans le monde.", "stars": 5},
                {"name": "Jardin Majorelle", "image": "assets/cities/jardin.jpg", "note": "Jardin botanique exotique.", "stars": 5},
                {"name": "Palais de la Bahia", "image": "assets/cities/bahiya.jpg", "note": "Palais royal moderne.", "stars": 4},
            ],
        },
        {
            "id": "rabat", "name": "Rabat", "subtitle": "Capitale Administrative",
            "description": "Capitale du Maroc, ville impériale alliant modernité et patrimoine. La Tour Hassan, le Mausolée Mohammed V et les jardins andalous vous plongent dans l'histoire du royaume.",
            "image": "assets/cities/rabat.png", "map_url": "https://maps.app.goo.gl/6qTnF4vBMepMcPJPA",
            "accent": [46, 125, 50],
            "stats": {"population": "580 000", "language": "Arabe, Berbère, Français", "currency": "MAD", "climate": "Tempéré océanique"},
            "location": {"lat": 34.0209, "lng": -6.8416},
            "restaurants": [
                {"name": "Le Dhow", "image": "assets/cities/dhow.jpg", "note": "Cuisine marocaine traditionnelle.", "stars": 5},
                {"name": "Yamal Acham", "image": "assets/cities/sofitelrabat.jpg", "note": "Spécialités syriennes et libanaises.", "stars": 4},
            ],
            "hotels": [
                {"name": "Sofitel Rabat Jardin des Roses", "image": "assets/cities/sofitel1.jpg", "note": "Hôtel 5 étoiles spa.", "stars": 5},
                {"name": "La Tour Hassan Palace", "image": "assets/cities/hassan.jpg", "note": "Palace historique.", "stars": 5},
            ],
            "transports": [
                {"name": "Train (ONCF)", "image": "assets/cities/rabat.png", "note": "ONCF"},
                {"name": "Tramway", "image": "assets/cities/rabat.png", "note": "Ligne Rabat-Salé"},
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "ALSA"},
            ],
            "places": [
                {"name": "Tour Hassan", "image": "assets/cities/hassan.jpg", "note": "Forteresse historique en bord de mer.", "stars": 5},
                {"name": "Chellah", "image": "assets/cities/chellah.jpg", "note": "Nécropole romaine en bordure de ville.", "stars": 4},
                {"name": "Kasbah des Oudayas", "image": "assets/cities/kasbah.jpg", "note": "Kasbah restaurée sur la colline.", "stars": 5},
            ],
        },
        {
            "id": "agadir", "name": "Agadir", "subtitle": "Plages et Soleil",
            "description": "Station balnéaire par excellence sur la côte atlantique. Plages de sable fin, soleil presque toute l'année et une multitude d'activités nautiques.",
            "image": "assets/cities/agadir.png", "map_url": "https://maps.app.goo.gl/YRy6LM9HrHhbkPvYA",
            "accent": [243, 156, 18],
            "stats": {"population": "420 000", "language": "Arabe, Berbère, Français, Anglais", "currency": "MAD", "climate": "Semi-aride côtier"},
            "location": {"lat": 30.4278, "lng": -9.5981},
            "restaurants": [
                {"name": "Le Jardin d'Eau", "image": "assets/cities/jardin.jpg", "note": "Cuisine marocaine traditionnelle.", "stars": 4},
                {"name": "Pure Passion", "image": "assets/cities/passion.jpg", "note": "Cuisine internationale et fruits de mer.", "stars": 5},
            ],
            "hotels": [
                {"name": "Sofitel Agadir Thalassa Sea & Spa", "image": "assets/cities/sofitel1.jpg", "note": "Hôtel de luxe face à l'océan.", "stars": 5},
                {"name": "Hotel Club Les Orangers", "image": "assets/cities/plage.jpg", "note": "Station balnéaire populaire.", "stars": 4},
            ],
            "transports": [
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "ALSA"},
                {"name": "Taxi", "image": "assets/cities/rabat.png", "note": "Petits et grands taxis"},
            ],
            "places": [
                {"name": "Plage d'Agadir", "image": "assets/cities/plage.jpg", "note": "Plage de sable fin très fréquentée.", "stars": 5},
                {"name": "Souk El Had", "image": "assets/cities/sooq.jpg", "note": "Plus grand marché d'Agadir.", "stars": 4},
                {"name": "Village d'artistes", "image": "assets/cities/nomad.jpg", "note": "Village d'artistes et artisans.", "stars": 4},
            ],
        },
        {
            "id": "essaouira", "name": "Essaouira", "subtitle": "Vent et Océan",
            "description": "Ancienne Mogador, cité portuaire historique classée UNESCO. Ses ruelles bleues et blanches, son port de pêche et ses plages ventées en font un havre de paix pour les artistes et les surfeurs.",
            "image": "assets/cities/essaouira.png", "map_url": "https://maps.app.goo.gl/KL2p2euk9sQB3CGT6",
            "accent": [52, 152, 219],
            "stats": {"population": "70 000", "language": "Arabe, Berbère, Français", "currency": "MAD", "climate": "Océanique tempéré"},
            "location": {"lat": 31.5085, "lng": -9.7595},
            "restaurants": [
                {"name": "Le Mandala", "image": "assets/cities/mandarine.jpg", "note": "Cuisine marocaine traditionnelle.", "stars": 4},
                {"name": "L'Atelier", "image": "assets/cities/atlant.jpg", "note": "Cuisine raffinée et produits locaux.", "stars": 4},
            ],
            "hotels": [
                {"name": "Sofitel Essaouira Mogador Golf & Spa", "image": "assets/cities/sofitel.jpg", "note": "Hôtel de luxe face à l'océan.", "stars": 5},
                {"name": "Riad Balima", "image": "assets/cities/balima.jpg", "note": "Riad authentique et luxueux.", "stars": 4},
            ],
            "transports": [
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "ALSA"},
                {"name": "Taxi", "image": "assets/cities/rabat.png", "note": "Petits et grands taxis"},
            ],
            "places": [
                {"name": "Médina d'Essaouira", "image": "assets/cities/swira.jpg", "note": "Ville historique fortifiée et préservée.", "stars": 5},
                {"name": "Port de pêche", "image": "assets/cities/dhow.jpg", "note": "Port animé aux barques bleues.", "stars": 4},
                {"name": "Plage de Sidi Kaouki", "image": "assets/cities/plagswira.jpg", "note": "Plages réputées pour le surf.", "stars": 4},
            ],
        },
        {
            "id": "chefchaouen", "name": "Chefchaouen", "subtitle": "La Ville Bleue",
            "description": "Perchée dans les montagnes du Rif, Chefchaouen est célèbre pour ses ruelles peintes en bleu. Une atmosphère paisible et des vues panoramiques à couper le souffle.",
            "image": "assets/cities/chefchaouen.png", "map_url": "https://maps.app.goo.gl/1kFqYfL2KJRZoYPL6",
            "accent": [41, 128, 185],
            "stats": {"population": "42 000", "language": "Arabe, Berbère, Français, Espagnol", "currency": "MAD", "climate": "Méditerranéen montagnard"},
            "location": {"lat": 35.1688, "lng": -5.2636},
            "restaurants": [
                {"name": "Beldi Bab Ssour", "image": "assets/cities/bab.jpg", "note": "Cuisine marocaine traditionnelle.", "stars": 4},
                {"name": "Café Haba", "image": "assets/cities/bleu.jpg", "note": "Terrasse avec vue imprenable.", "stars": 4},
            ],
            "hotels": [
                {"name": "Riad Hicham", "image": "assets/cities/riad2.jpg", "note": "Riad traditionnel avec patio.", "stars": 4},
                {"name": "Hotel Barcelona", "image": "assets/cities/kasbah1.jpg", "note": "Hôtel de charme.", "stars": 3},
            ],
            "transports": [
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "CTM / Supratours"},
                {"name": "Taxi", "image": "assets/cities/rabat.png", "note": "Petits taxis"},
            ],
            "places": [
                {"name": "Médina bleue", "image": "assets/cities/bleu.jpg", "note": "Ruelles pittoresques de la médina.", "stars": 5},
                {"name": "Kasbah", "image": "assets/cities/kasbah.jpg", "note": "Kasbah restaurée sur la colline.", "stars": 4},
                {"name": "Mosquée espagnole", "image": "assets/cities/scala.jpg", "note": "Point de vue panoramique.", "stars": 4},
            ],
        },
        {
            "id": "fes", "name": "Fès", "subtitle": "Capitale Spirituelle",
            "description": "Plus ancienne ville impériale, Fès abrite la plus vieille université du monde (Al Quaraouiyine). Sa médina labyrinthique et ses tanneries colorées sont un voyage dans le temps.",
            "image": "assets/cities/fes.png", "map_url": "https://maps.app.goo.gl/eC1GVtQg1fGJK7meA",
            "accent": [211, 84, 0],
            "stats": {"population": "1,1 million", "language": "Arabe, Berbère, Français", "currency": "MAD", "climate": "Continental semi-aride"},
            "location": {"lat": 34.0181, "lng": -5.0078},
            "restaurants": [
                {"name": "Riad Fès", "image": "assets/cities/riad.jpg", "note": "Cuisine marocaine raffinée.", "stars": 5},
                {"name": "Maison Bleue", "image": "assets/cities/bleu.jpg", "note": "Palais restauré avec fresques.", "stars": 5},
            ],
            "hotels": [
                {"name": "Palais Amani", "image": "assets/cities/palace.jpg", "note": "Palais restauré avec fresques.", "stars": 5},
                {"name": "Riad Laaroussa", "image": "assets/cities/riad2.jpg", "note": "Riad authentique et luxueux.", "stars": 5},
            ],
            "transports": [
                {"name": "Train (ONCF)", "image": "assets/cities/rabat.png", "note": "ONCF"},
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "ALSA"},
                {"name": "Taxi", "image": "assets/cities/rabat.png", "note": "Petits et grands taxis"},
            ],
            "places": [
                {"name": "Médina de Fès", "image": "assets/cities/fes1.jpg", "note": "Ville sainte et lieu de pèlerinage.", "stars": 5},
                {"name": "Tannerie Chouara", "image": "assets/cities/chouara.jpg", "note": "Tannerie historique en activité.", "stars": 4},
                {"name": "Université Al Quaraouiyine", "image": "assets/cities/univi.jpg", "note": "Université millénaire.", "stars": 5},
            ],
        },
        {
            "id": "tanger", "name": "Tanger", "subtitle": "Ville entre Deux Mers",
            "description": "Carrefour stratégique entre l'Europe et l'Afrique, Tanger séduit par son port mythique, ses plages dorées et sa médina cosmopolite. Le détroit de Gibraltar offre un spectacle unique.",
            "image": "assets/cities/tanger.png", "map_url": "https://maps.app.goo.gl/f1DkfCgjzSRVj8Hv6",
            "accent": [155, 89, 182],
            "stats": {"population": "1 million", "language": "Arabe, Berbère, Français, Espagnol, Anglais", "currency": "MAD", "climate": "Méditerranéen"},
            "location": {"lat": 35.7673, "lng": -5.7998},
            "restaurants": [
                {"name": "Le Saveur du Poisson", "image": "assets/cities/poisson.jpg", "note": "Cuisine de poisson frais.", "stars": 4},
                {"name": "Dar Naji", "image": "assets/cities/dinarjat.jpg", "note": "Cuisine marocaine traditionnelle.", "stars": 4},
            ],
            "hotels": [
                {"name": "El Minzah Hotel", "image": "assets/cities/hotel.jpg", "note": "Hôtel de luxe historique.", "stars": 5},
                {"name": "Hilton Tanger City Center", "image": "assets/cities/hotel.jpg", "note": "Hôtel moderne centre-ville.", "stars": 5},
            ],
            "transports": [
                {"name": "Train (ONCF)", "image": "assets/cities/rabat.png", "note": "ONCF (LGV Al Boraq)"},
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "ALSA"},
                {"name": "Taxi", "image": "assets/cities/rabat.png", "note": "Petits et grands taxis"},
            ],
            "places": [
                {"name": "Cap Spartel", "image": "assets/cities/cornich.jpg", "note": "Phare et promenade en bord de mer.", "stars": 4},
                {"name": "Grottes d'Hercule", "image": "assets/cities/grotte.jpg", "note": "Cave naturelle pittoresque.", "stars": 4},
                {"name": "Médina de Tanger", "image": "assets/cities/tange.jpg", "note": "Ruelles pittoresques de la médina.", "stars": 4},
            ],
        },
        {
            "id": "merzouga", "name": "Merzouga", "subtitle": "Porte du Sahara",
            "description": "Aux portes du désert du Sahara, Merzouga offre un spectacle inoubliable : les dunes de sable de l'Erg Chebbi qui changent de couleur au lever et coucher du soleil.",
            "image": "assets/cities/merzouga.png", "map_url": "https://maps.app.goo.gl/XsXwDTjeYHh2HVq98",
            "accent": [243, 156, 18],
            "stats": {"population": "3 000", "language": "Arabe, Berbère, Français, Anglais", "currency": "MAD", "climate": "Désertique aride"},
            "location": {"lat": 31.1102, "lng": -4.0110},
            "restaurants": [
                {"name": "Chez Julia", "image": "assets/cities/chebbi.jpg", "note": "Cuisine marocaine traditionnelle.", "stars": 4},
                {"name": "Riad Erg Chebbi", "image": "assets/cities/chebbi.jpg", "note": "Cuisine marocaine raffinée.", "stars": 4},
            ],
            "hotels": [
                {"name": "Kasbah Erg Chebbi", "image": "assets/cities/chebbi.jpg", "note": "Hébergement chez l'habitant.", "stars": 4},
                {"name": "Auberge du Désert", "image": "assets/cities/chemeau.jpg", "note": "Excursions en 4x4 et balade à dromadaire.", "stars": 3},
            ],
            "transports": [
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "CTM / Supratours"},
                {"name": "4x4", "image": "assets/cities/rabat.png", "note": "Excursions 4x4"},
            ],
            "places": [
                {"name": "Erg Chebbi", "image": "assets/cities/chebbi.jpg", "note": "Dunes de sable spectaculaires.", "stars": 5},
                {"name": "Coucher de soleil sur les dunes", "image": "assets/cities/chebbi.jpg", "note": "Coucher de soleil inoubliable.", "stars": 5},
                {"name": "Khamlia", "image": "assets/cities/nomad.jpg", "note": "Village nomade et musique gnawa.", "stars": 4},
            ],
        },
        {
            "id": "ouarzazate", "name": "Ouarzazate", "subtitle": "Hollywood du Maroc",
            "description": "Surnommée la porte du désert, Ouarzazate est un centre majeur de production cinématographique. Ses kasbahs en brique crue et ses paysages lunaires attirent réalisateurs et voyageurs.",
            "image": "assets/cities/ouarzazate.png", "map_url": "https://maps.app.goo.gl/eC1GVtQg1fGJK7meA",
            "accent": [192, 57, 43],
            "stats": {"population": "70 000", "language": "Arabe, Berbère, Français", "currency": "MAD", "climate": "Désertique semi-aride"},
            "location": {"lat": 30.9203, "lng": -6.8935},
            "restaurants": [
                {"name": "La Kasbah", "image": "assets/cities/kasbah.jpg", "note": "Cuisine marocaine traditionnelle.", "stars": 4},
                {"name": "Le Petit Riad", "image": "assets/cities/riad2.jpg", "note": "Cuisine raffinée.", "stars": 4},
            ],
            "hotels": [
                {"name": "Kasbah de Ouarzazate", "image": "assets/cities/kasbahh.jpg", "note": "Kasbah historique en brique crue.", "stars": 4},
                {"name": "Hotel La Gazelle", "image": "assets/cities/kasbah1.jpg", "note": "Hôtel de charme.", "stars": 4},
            ],
            "transports": [
                {"name": "Bus", "image": "assets/cities/rabat.png", "note": "CTM / Supratours"},
                {"name": "Taxi", "image": "assets/cities/rabat.png", "note": "Grands taxis"},
            ],
            "places": [
                {"name": "Kasbah Aït Ben Haddou", "image": "assets/cities/kasbahh.jpg", "note": "Village fortifié (ksar) historique.", "stars": 5},
                {"name": "Atlas Studios", "image": "assets/cities/studio.jpg", "note": "Studio de cinéma en activité.", "stars": 4},
                {"name": "Kasbah Taourirt", "image": "assets/cities/kasbah1.jpg", "note": "Kasbah historique en brique crue.", "stars": 4},
            ],
        },
    ]


def seed_cities():
    """Insert default cities if table is empty"""
    conn = _connect()
    if not conn:
        return
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as cnt FROM cities")
        row = cursor.fetchone()
        if row and row["cnt"] > 0:
            return
        cities = _default_cities()
        for c in cities:
            save_city(c)
        log.info(f"Seeded {len(cities)} cities")
    except mysql.connector.Error as e:
        log.error(f"seed_cities error: {e}")
    finally:
        _close(cursor, conn)


def _close(cursor, conn):
    try:
        if cursor: cursor.close()
    except Exception:
        pass
    try:
        if conn: conn.close()
    except Exception:
        pass


def _row_to_city(row):
    if not row:
        return None
    return {
        "id": row[0],
        "name": row[1],
        "subtitle": row[2] or "",
        "description": row[3] or "",
        "image": row[4] or "",
        "map_url": row[5] or "",
        "accent": json.loads(row[6]) if row[6] else [82, 116, 158],
        "stats": {
            "population": row[7] or "",
            "language": row[8] or "",
            "currency": row[9] or "MAD",
            "climate": row[10] or "",
        },
        "location": {
            "lat": row[11] or 0,
            "lng": row[12] or 0,
        },
        "restaurants": json.loads(row[13]) if row[13] else [],
        "hotels": json.loads(row[14]) if row[14] else [],
        "transports": json.loads(row[15]) if row[15] else [],
        "places": json.loads(row[16]) if row[16] else [],
    }


def get_all_cities() -> List[Dict[str, Any]]:
    conn = _connect()
    if not conn:
        return []
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities")
        rows = cursor.fetchall()
        return [_row_to_city(r) for r in rows]
    except mysql.connector.Error as e:
        log.error(f"get_all_cities error: {e}")
        return []
    finally:
        _close(cursor, conn)


def get_city(city_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE id = %s", (city_id,))
        row = cursor.fetchone()
        return _row_to_city(row)
    except mysql.connector.Error as e:
        log.error(f"get_city error: {e}")
        return None
    finally:
        _close(cursor, conn)


def save_city(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM cities WHERE id = %s", (data["id"],))
        exists = cursor.fetchone()
        stats = data.get("stats", {})
        loc = data.get("location", {})
        accent = json.dumps(data.get("accent", [82, 116, 158]))
        restaurants = json.dumps(data.get("restaurants", []))
        hotels = json.dumps(data.get("hotels", []))
        transports = json.dumps(data.get("transports", []))
        places = json.dumps(data.get("places", []))
        if exists:
            cursor.execute("""
                UPDATE cities SET
                    name=%s, subtitle=%s, description=%s, image=%s, map_url=%s,
                    accent=%s, population=%s, language=%s, currency=%s, climate=%s,
                    lat=%s, lng=%s, restaurants=%s, hotels=%s, transports=%s, places=%s
                WHERE id=%s
            """, (
                data["name"], data.get("subtitle",""), data.get("description",""),
                data.get("image",""), data.get("map_url",""),
                accent, stats.get("population",""), stats.get("language",""),
                stats.get("currency","MAD"), stats.get("climate",""),
                loc.get("lat",0), loc.get("lng",0),
                restaurants, hotels, transports, places,
                data["id"],
            ))
        else:
            cursor.execute("""
                INSERT INTO cities (id, name, subtitle, description, image, map_url,
                    accent, population, language, currency, climate,
                    lat, lng, restaurants, hotels, transports, places)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                data["id"], data["name"], data.get("subtitle",""),
                data.get("description",""), data.get("image",""), data.get("map_url",""),
                accent, stats.get("population",""), stats.get("language",""),
                stats.get("currency","MAD"), stats.get("climate",""),
                loc.get("lat",0), loc.get("lng",0),
                restaurants, hotels, transports, places,
            ))
        conn.commit()
        return data
    except mysql.connector.Error as e:
        log.error(f"save_city error: {e}")
        return None
    finally:
        _close(cursor, conn)


def delete_city(city_id: str) -> bool:
    conn = _connect()
    if not conn:
        return False
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cities WHERE id = %s", (city_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        return deleted
    except mysql.connector.Error as e:
        log.error(f"delete_city error: {e}")
        return False
    finally:
        _close(cursor, conn)


def add_item(city_id: str, section: str, item: Dict[str, Any]) -> Optional[Dict]:
    city = get_city(city_id)
    if not city:
        return None
    items = city.setdefault(section, [])
    items.append(item)
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE cities SET `{section}`=%s WHERE id=%s", (json.dumps(items), city_id))
        conn.commit()
        return item
    except mysql.connector.Error as e:
        log.error(f"add_item error: {e}")
        return None
    finally:
        _close(cursor, conn)


def update_item(city_id: str, section: str, idx: int, item: Dict) -> Optional[Dict]:
    city = get_city(city_id)
    if not city:
        return None
    items = city.get(section, [])
    if 0 <= idx < len(items):
        items[idx] = item
        conn = _connect()
        if not conn:
            return None
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE cities SET `{section}`=%s WHERE id=%s", (json.dumps(items), city_id))
            conn.commit()
            return item
        except mysql.connector.Error as e:
            log.error(f"update_item error: {e}")
            return None
        finally:
            _close(cursor, conn)
    return None


def delete_item(city_id: str, section: str, idx: int) -> bool:
    city = get_city(city_id)
    if not city:
        return False
    items = city.get(section, [])
    if 0 <= idx < len(items):
        items.pop(idx)
        conn = _connect()
        if not conn:
            return False
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE cities SET `{section}`=%s WHERE id=%s", (json.dumps(items), city_id))
            conn.commit()
            return True
        except mysql.connector.Error as e:
            log.error(f"delete_item error: {e}")
            return False
        finally:
            _close(cursor, conn)
    return False


def add_reservation(res):
    conn = _connect()
    if not conn:
        res["id"] = 0
        res["status"] = "pending"
        return res
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reservations (name, email, phone, birthdate,
                city_id, city_name, category, item_name, date_res,
                nights, persons, total, menu_items, created_at, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            res.get("name",""), res.get("email",""),
            res.get("phone",""), res.get("birthdate",""),
            res.get("city_id",""), res.get("city_name",""),
            res.get("category",""), res.get("item_name",""),
            res.get("date_res",""), res.get("nights",""), res.get("persons",""),
            res.get("total",""), json.dumps(res.get("menu_items","")),
            res.get("created_at",""), "pending",
        ))
        res_id = cursor.lastrowid
        conn.commit()
        res["id"] = res_id
        res["status"] = "pending"
        return res
    except mysql.connector.Error as e:
        log.error(f"add_reservation error: {e}")
        res["id"] = 0
        res["status"] = "pending"
        return res
    finally:
        _close(cursor, conn)


def get_reservations(status=None):
    conn = _connect()
    if not conn:
        return []
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        if status:
            cursor.execute("SELECT * FROM reservations WHERE status = %s ORDER BY id DESC", (status,))
        else:
            cursor.execute("SELECT * FROM reservations ORDER BY id DESC")
        rows = cursor.fetchall()
        for r in rows:
            if r.get("menu_items") and isinstance(r["menu_items"], str):
                try:
                    r["menu_items"] = json.loads(r["menu_items"])
                except:
                    pass
        return rows
    except mysql.connector.Error as e:
        log.error(f"get_reservations error: {e}")
        return []
    finally:
        _close(cursor, conn)


def get_reservation(res_id):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reservations WHERE id = %s", (res_id,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        log.error(f"get_reservation error: {e}")
        return None
    finally:
        _close(cursor, conn)


def add_user(data):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""INSERT INTO users (first_name, last_name, email, country, phone, birthdate, password, created_at)
                          VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                       (data["first_name"], data["last_name"], data["email"],
                        data["country"], data.get("phone",""), data.get("birthdate",""),
                        data["password"], datetime.now().isoformat()))
        conn.commit()
        return {"id": cursor.lastrowid}
    except mysql.connector.Error as e:
        log.error(f"add_user error: {e}")
        raise
    finally:
        _close(cursor, conn)


def get_user_by_email(email):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cursor.fetchone()
    except mysql.connector.Error as e:
        log.error(f"get_user_by_email error: {e}")
        return None
    finally:
        _close(cursor, conn)


def update_reservation_status(res_id, status):
    conn = _connect()
    if not conn:
        return None
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reservations WHERE id = %s", (res_id,))
        r = cursor.fetchone()
        if r:
            cursor.execute("UPDATE reservations SET status = %s WHERE id = %s", (status, res_id))
            conn.commit()
        return r
    except mysql.connector.Error as e:
        log.error(f"update_reservation_status error: {e}")
        return None
    finally:
        _close(cursor, conn)
