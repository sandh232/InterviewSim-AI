from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from app.interview_graph import run_interview

##### 1. Initializing Flask application #####
# __name__variable tells Flask where to find the app’s files
app = Flask(__name__)

# Initializing a session store that will store user conversation states, 
# mapping each user’s WhatsApp number to their session data
user_sessions = {}

##### 2. Creating Webhook Endpoint #####
# creating a webhook that Twilio calls when a WhatsApp message arrives
@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Webhook endpoint for Twilio WhatsApp messages.
    Processes incoming messages and returns appropriate responses using the agent.
    """
    try:
        # Get incoming message details
        incoming_msg = request.values.get('Body', '').strip()
        sender = request.values.get('From', '')
        # Initialize response
        resp = MessagingResponse()
        # Ensure sender is present
        if not sender or not incoming_msg:
            resp.message("Sorry, I couldn't process your message. Please try again.")
            return str(resp)
        # Use run_interview to process the message and get a response
        response = run_interview(sender, incoming_msg, user_sessions)
        resp.message(response)
        return str(resp)
    except Exception:
        # Return a generic error message to the user (no system details)
        resp = MessagingResponse()
        resp.message("Sorry, something went wrong. Please try again later.")
        return str(resp)

