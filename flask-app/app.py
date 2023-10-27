from flask import *
import postgresqlite
import sqlalchemy as sa
import datetime
from flask_mail import *
import requests
import traceback 
import json
import logging
import secrets
import os
import pickle

# source ~/.venvs/flask/bin/activate

app = Flask(__name__, template_folder='templates')

# Flask-Mail configuration for Outlook
app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

logging.basicConfig(filename= os.getenv("DIRECTORY_LOG"), level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# Configure Flask app settings
app.config['SECRET_KEY'] = secrets.token_hex(16)

@app.errorhandler(Exception)
def internal_server_error(e):
    """
    Description:
        Runs when there is an error. Logs the error and provides a user-friendly error message.

    Args:
        e (Exception): The error object.

    Returns:
        A rendered template with an error message.
    """
    error_message = str(e)
    traceback_info = traceback.format_exc().strip().split("\n")
    traceback_info = [string.replace('^', '') for string in traceback_info]

    response = {
        "message": error_message,
        "traceback": traceback_info
    }

    send_email(response)
    
    app.logger.error(response)  # Log the error to record.log
    flash('An error occurred')
    
    return render_template('auth/error.html', error_message=response)


def send_email(response):
    try:
        # Establish the SMTP connection
        with app.app_context():
            mail.connect()

            # Create the email message
            msg = Message('There has been an error', sender=os.getenv("MAIL_USERNAME"), recipients=[os.getenv("MAIL_USERNAME")])
            msg.body = f"{response}"

            # Send the email
            mail.send(msg)

            # Disconnect after sending the email
            mail.disconnect()

        return 'Email sent!'
    except Exception as e:
        return f'Error: {str(e)}'

def add_to_session(api_data: dict, data : dict):
    """
    Description:
        Adds info from the API response to the session and stores it in a JSON file.

    Args:
        api_data (dict): API response data.

    Returns:
        None
    """
    for key, value in api_data.items():
        if key == "id" or key in session.get('data', {}):
            continue
        data[key] = value

    if data:
        session['data'] = data  # Store the data in the session

        # Open the file in binary mode for appending binary data
        with open(os.getenv("FILE_LOG"), 'ab+') as fp:
            # Move the cursor to the end of the file
            fp.seek(0, 2)
            
            # Use pickle.dump() to serialize and write the data as binary
            pickle.dump(data, fp)

        response = f"Data fetched and stored in session successfully at {datetime.datetime.now()}"
        app.logger.info(response)

    else:
        return None

@app.route("/show", methods=["GET", "POST"])
def show():
    #To load from pickle file
    data = []
    with open(os.getenv("FILE_LOG"), 'rb') as fr:
        try:
            while True:
                data.append(pickle.load(fr))
        except EOFError:
            pass

    return render_template('blog/dashboard.html', api_data_list=data)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            data = {}
            api_data = request.get_json()  # Get JSON data from the POST request
            add_to_session(api_data, data)  # Add data to session
            idorder = str(session.get('data', {}).get('picklist', {}).get('idorder'))

            # Get API URL from environment variable
            api_url = os.getenv("API_URL") + idorder
            api_url = api_url.replace('"','')

            # Making a GET request with basic authentication
            response = requests.get(api_url, auth=(os.getenv("API_KEY_PICKER"), ''))
            api_data = response.json()
            add_to_session(api_data, data)  # Update session data

            test = session.get('data', {}).get('invoicecountry')

            data = {
                "Customer": {
                    "CollectionLocation": os.getenv("COLLECTION_LOCATION"),
                    "ContactPerson": os.getenv("CONTACT_PERSON"),
                    "CustomerCode": os.getenv("CUSTOMER_CODE"),
                    "CustomerNumber": os.getenv("CUSTOMER_NUMBER"),
                    "Email": os.getenv("EMAIL"),
                    "Name": os.getenv("NAME")
                },
                "Message": {
                    "MessageID": "1",
                    "MessageTimeStamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                    "Printertype": "GraphicFile|PDF"
                },
                "Shipments": [
                    {
                        "Addresses": [
                            {
                                "AddressType": "02",
                                "City": session.get('data', {}).get('invoicecity'),
                                "CompanyName": session.get('data', {}).get('invoicename'),
                                "Countrycode": session.get('data', {}).get('invoicecountry'),
                                "Name": session.get('data', {}).get('picklist', {}).get('deliveryname'),
                                "StreetHouseNrExt": session.get('data', {}).get('invoiceaddress'),
                                "Zipcode": session.get('data', {}).get('invoicecity')
                            },
                            {
                                "AddressType": "01",
                                "City": session.get('data', {}).get('picklist', {}).get('deliverycity'),
                                "CompanyName": session.get('data', {}).get('picklist', {}).get('deliveryname'),
                                "Countrycode": session.get('data', {}).get('picklist', {}).get('deliverycountry'),
                                "Name": session.get('data', {}).get('picklist', {}).get('deliveryname'),
                                "StreetHouseNrExt": session.get('data', {}).get('picklist', {}).get('deliveryaddress'),
                                "Zipcode": session.get('data', {}).get('picklist', {}).get('deliveryzipcode')
                            }
                        ],
                        "Contacts": [
                            {
                                "ContactType": "01",
                                "Email": session.get('data', {}).get('picklist', {}).get('emailaddress'),
                                "TelNr": session.get('data', {}).get('picklist', {}).get('telephone')
                            }
                        ],
                        "Dimension": {
                            "Weight": session.get('data', {}).get('weight')
                        },
                        "ProductCodeDelivery": "3189"
                    }
                ]
            }

            # Authentication credentials (replace 'YOUR_API_KEY' with your actual API key)
            api_key = 'MeXi0GWVeHDiWB4wWW0EoehDAPnfBOtB'

            # Prepare the headers with the API key
            headers = {
                'apikey': api_key,
                'Content-Type': 'application/json'
            }

            # Make the API request with headers
            response = requests.post("https://api-sandbox.postnl.nl/shipment/v2_2/label", headers=headers, json=data)

            api_data = response.json()

            return api_data


        except Exception as e:
            return internal_server_error(e)  # Handle exceptions

    else:
        return render_template('blog/dashboard.html')


if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)
