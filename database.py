import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # Use the external database URL which has the full domain name
    return psycopg2.connect(os.getenv("EXTERNAL_DATABASE_URL"))