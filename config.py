import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "cities")

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
FLASK_DEBUG = False
FLASK_PORT = 5000

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "marwan2007")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "apikey")
SMTP_PASS = os.environ.get("SMTP_PASS", os.environ.get("SENDGRID_API_KEY", ""))
SMTP_FROM = os.environ.get("SMTP_FROM", "guidtoristique@gmail.com")

MYSQL_HOST = os.environ.get("MYSQLHOST", os.environ.get("MYSQL_HOST", "localhost"))
MYSQL_PORT = int(os.environ.get("MYSQLPORT", os.environ.get("MYSQL_PORT", "3306")))
MYSQL_USER = os.environ.get("MYSQLUSER", os.environ.get("MYSQL_USER", "root"))
MYSQL_PASS = os.environ.get("MYSQLPASSWORD", os.environ.get("MYSQL_PASS", ""))
MYSQL_DB = os.environ.get("MYSQLDATABASE", os.environ.get("MYSQL_DB", "tourist_guide"))

SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:5000")

LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")
LOG_LEVEL = "INFO"
