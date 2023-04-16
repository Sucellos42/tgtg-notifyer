import threading

from dotenv import load_dotenv
import os
import random
import time
from flask import Flask, jsonify
from pushbullet import Pushbullet
from tgtg import TgtgClient
from tgtg.exceptions import TgtgAPIError, TgtgLoginError

app = Flask(__name__)

# load environment variables from .env file
load_dotenv()

# TGTG client configuration
TGTG_ACCESS_TOKEN = os.getenv('TGTG_ACCESS_TOKEN')
TGTG_REFRESH_TOKEN = os.getenv('TGTG_REFRESH_TOKEN')
TGTG_USER_ID = os.getenv('TGTG_USER_ID')
TGTG_COOKIE = os.getenv('TGTG_COOKIE')

client = TgtgClient(
    access_token=TGTG_ACCESS_TOKEN,
    refresh_token=TGTG_REFRESH_TOKEN,
    user_id=TGTG_USER_ID,
    cookie=TGTG_COOKIE
)

# Pushbullet configuration
PUSHBULLET_ACCESS_TOKEN = os.getenv('PUSHBULLET_ACCESS_TOKEN')
pb = Pushbullet(PUSHBULLET_ACCESS_TOKEN)


def send_bullet(title, message):
    try:
        push = pb.push_note(title, message)
        print(f"Notification sent: {push}")
    except Exception as e:
        print(f"Error sending Pushbullet notification: {e}")


def is_access_token_valid():
    try:
        client.get_items()
        return True
    except TgtgAPIError as e:
        print(f"Error checking access token: {e}")
    except Exception as e:
        print(f"Error checking access token: {e}")
        return False


def check_items_and_send_sms():
    if not is_access_token_valid():
        send_bullet("ERROR: ", "Access token is not valid. Please refresh the token.")
        return

    try:
        items = client.get_items()
        available_items = []

        for item in items:
            time.sleep(5)  # Ajout d'un intervalle de 5 secondes entre chaque appel d'item
            if item["items_available"] > 0:
                print(f"{item['display_name']} is available")
                available_items.append(item['display_name'])
            else:
                print(f"{item['display_name']} is not available")

        if available_items:
            message = "\n" + "\n".join(available_items)
            send_bullet("Items available", message)
        else:
            print("No items available")

    except Exception as e:
        print(f"Error fetching items: {e}")


def print_remaining_time(start_time, delay):
    remaining_time = int(delay - (time.time() - start_time))
    if remaining_time > 0:
        print(f"Temps restant avant le prochain check: {remaining_time} secondes")
        threading.Timer(10, print_remaining_time, [start_time, delay]).start()


def schedule_check():
    delay = random.randint(60, 433)  # Générer un nombre aléatoire entre 60 et 120 secondes (1 à 2 minutes)
    print(f"Next check in {delay} seconds.")
    print_remaining_time(time.time(), delay)
    time.sleep(delay)
    check_items_and_send_sms()
    schedule_check()


def start_schedule_check_in_thread():
    print("Starting scheduled checks")
    check_thread = threading.Thread(target=schedule_check)
    check_thread.start()


@app.route('/')
def home():
    return jsonify({"message": "Server is running"}), 200


if __name__ == '__main__':
    print("Starting scheduled checks")
    start_schedule_check_in_thread()
    app.run(port=5001)
