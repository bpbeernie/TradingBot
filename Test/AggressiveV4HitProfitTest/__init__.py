from Mail import Email

Email.PATH_TO_CRED = "../../Mail/credentials.json"

def _new_send_message(destination, obj, body):
    print("Sending Email")

Email.send_message = _new_send_message