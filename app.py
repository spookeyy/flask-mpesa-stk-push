import base64
import datetime
from flask import Flask, request
import requests
from requests.auth import HTTPBasicAuth
import os

app = Flask(__name__)

# Get environment variables
consumer_key = os.getenv('MPESA_CONSUMER_KEY')
consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
mpesa_shortcode = os.getenv('MPESA_SHORTCODE')
mpesa_pass_key = os.getenv('MPESA_PASS_KEY')
mpesa_token_url = os.getenv('MPESA_TOKEN_URL')

@app.route('/')
def index():
    return "Spookie's Mpesa Integration service"

my_endpoint = "https://webhook.site/9e1a6307-9adc-465b-a37b-78db245785a7"

# simulate
@app.route('/pay', methods=['POST', 'GET'])
def MpesaExpress():
    amount = request.args.get('amount')
    phone = request.args.get('phone')

    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif not phone.startswith('254'):
        phone = '254' + phone

    if not phone.isdigit():
        return {"error": "Phone number must contain only digits"}, 400
        
    if len(phone) < 9 or len(phone) > 12:
        return {"error": "Invalid phone number length"}, 400
        
    try:
        amount_value = float(amount)
        if amount_value <= 0:
            return {"error": "Amount must be greater than 0"}, 400
    except ValueError:
        return {"error": "Invalid amount value"}, 400
    
    access_token = getAccessToken()
    if not access_token:
        return {"error": "Failed to get access token"}, 500
    
    endpoint = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    password = f"{mpesa_shortcode}{mpesa_pass_key}{timestamp}"
    password = base64.b64encode(password.encode('utf-8')).decode('utf-8')

    payload = {
        "BusinessShortCode": mpesa_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": mpesa_shortcode,
        "PhoneNumber": phone,
        "CallBackURL": my_endpoint + "/callback",
        "AccountReference": "Marps Africa",
        "TransactionDesc": "Payment of X"
    }

    response = requests.post(endpoint, json=payload, headers=headers)
    return response.json()

@app.route("/callback", methods=['POST'])
def callback():
    data = request.get_json()
    app.logger.info(f"Callback data: {data}")
    print(f"Full callback request: {request.headers}\n{data}")
    return data, 200

def getAccessToken():
    try:
        # Using the global variables directly
        global consumer_key, consumer_secret, mpesa_token_url
        
        if not consumer_key or not consumer_secret:
            print("Error: MPESA_CONSUMER_KEY or MPESA_CONSUMER_SECRET environment variables not set")
            consumer_key = os.getenv('MPESA_CONSUMER_KEY')
            consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        
        # print(f"Using Consumer Key: {consumer_key[:5]}...")
        # print(f"Using Consumer Secret: {consumer_secret[:5]}...")
        # print(f"Requesting access token from {mpesa_token_url}")
        
        res = requests.get(mpesa_token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        
        # Check for HTTP errors
        res.raise_for_status()
        
        # for debugging
        print(f"Response status: {res.status_code}")
        print(f"Response content: {res.text[:100]}...")
        
        data = res.json()
        return data['access_token']
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except ValueError as e:
        print(f"JSON parsing failed: {e}")
        if 'res' in locals():
            print(f"Full response: {res.text}")
        return None
    except KeyError as e:
        print(f"Key not found in response: {e}")
        print(f"Response data: {data}")
        return None

if __name__ == '__main__':
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded environment variables from .env file")
    except ImportError:
        print("dotenv package not installed, skipping .env file loading")
    
    app.run(host='0.0.0.0', port=5000, debug=True)