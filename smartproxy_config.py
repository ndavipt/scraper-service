import os
from dotenv import load_dotenv

load_dotenv()

def get_smartproxy_proxies():
    # Let's try using the API directly instead of the proxy
    return None

def get_smartproxy_api_headers():
    """Returns headers needed for SmartProxy API requests"""
    token = os.getenv("SMARTPROXY_AUTH_TOKEN")
    return {
        "Accept": "application/json",
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json"
    }