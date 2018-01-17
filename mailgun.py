import requests

API_KEY = "APIKEY"


def send_account_verification(message, to):
    return requests.post(
        "https://api.mailgun.net/v3/mg.greatmoves.xyz/messages",
        auth=("api", API_KEY),
        data={"from": "Great Moves! Account Verification <verify@greatmoves.xyz>",
              "to": [to],
              "subject": "Verify your account",
              "html": message})


def send_password_reset(message, to):
    return requests.post(
        "https://api.mailgun.net/v3/mg.greatmoves.xyz/messages",
        auth=("api", API_KEY),
        data={"from": "Great Moves! Password Reset <password@greatmoves.xyz>",
              "to": [to],
              "subject": "Reset your password",
              "html": message})
