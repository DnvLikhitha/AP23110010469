import os
import sys

# Add the parent directory to sys.path so we can import logging_middleware from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from dotenv import load_dotenv
from datetime import datetime
from logging_middleware.logger import app_logger

# Load environment variables
load_dotenv(override=True)
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

AUTH_HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Priority weights according to Stage 6 rules
PRIORITY_WEIGHTS = {
    "Placement": 3,
    "Result": 2,
    "Event": 1
}

def fetch_all_notifications():
    app_logger.info("Fetching notifications from API...")
    url = "http://20.207.122.201/evaluation-service/notifications"
    response = requests.get(url, headers=AUTH_HEADERS)
    response.raise_for_status()
    return response.json().get("notifications", [])
    
def sort_priority(item):
    # Get the weight score, default to 0 if unknown type
    type_score = PRIORITY_WEIGHTS.get(item["Type"], 0)
    
    # Convert timestamp string to datetime object so we can sort by latest time
    time_obj = datetime.strptime(item["Timestamp"], "%Y-%m-%d %H:%M:%S")
    
    return (type_score, time_obj)

def get_priority_inbox(n: int = 10):
    all_notifs = fetch_all_notifications()
    
    # Sort backwards (descending weight score, then descending date)
    sorted_notifs = sorted(all_notifs, key=sort_priority, reverse=True)
    
    # Take the top n elements
    return sorted_notifs[:n]
    
if __name__ == "__main__":
    top_10 = get_priority_inbox(10)
    
    app_logger.info("--- PRIORITY INBOX (TOP 10) ---")
    for index, notif in enumerate(top_10, 1):
        app_logger.info(f"{index}. [{notif['Type']}] - {notif['Message']} (Sent: {notif['Timestamp']})")