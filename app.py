from dotenv import load_dotenv
import os
import schedule
import time
import random

from flask import Flask, jsonify
from pushbullet import Pushbullet
from tgtg import TgtgClient
from tgtg.exceptions import TgtgAPIError, TgtgLoginError
from twilio.rest import Client

app = Flask(__name__)

# load environment variables from .env file
load_dotenv()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
MY_PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER')

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

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


def get_next_run_time():
    if not schedule.get_jobs():
        return None

    next_run_time = min(job.next_run for job in schedule.get_jobs())
    return next_run_time


def display_next_schedule():
    next_check = get_next_run_time()
    if next_check:
        print(f"Next check: {next_check}")
    else:
        print("No scheduled jobs.")


def reschedule():
    delay = random.randint(0, 600)  # Générer un nombre aléatoire entre 0 et 600 secondes (10 minutes)
    minutes, seconds = divmod(delay, 60)  # Convertir les secondes en minutes et secondes
    print(f"Next check in {minutes} minutes and {seconds} seconds.")
    schedule.every(5).seconds.do(
        check_items_and_send_sms
    )  # Planifier le prochain check avec le délai en secondes
    print("Checking items...")


def send_sms(message):
    try:
        message = twilio_client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=MY_PHONE_NUMBER
        )
        print(f"SMS sent: {message.sid}")
    except Exception as e:
        print(f"Error sending SMS: {e}")


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
        # if e. == 401:  # Unauthorized
        #     return False
        # else:
        #     raise e
    except Exception as e:
        print(f"Error checking access token: {e}")
        return False


def check_items_and_send_sms():
    if not is_access_token_valid():
        # send_sms("Access token is not valid. Please refresh the token.")
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
            # send_sms(message)
            send_bullet("Items available", message)
        else:
            print("No items available")

    except Exception as e:
        print(f"Error fetching items: {e}")

    reschedule()


@app.route('/')
def home():
    check_items_and_send_sms()
    return jsonify({"message": "Check executed"}), 200


if __name__ == '__main__':
    # schedule.every(1).minutes.do(check_items_and_send_sms)
    reschedule()

    while True:
        schedule.run_pending()
        time.sleep(1)
