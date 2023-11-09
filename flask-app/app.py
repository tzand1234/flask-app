from flask import Flask, flash, session, request, jsonify, send_file
import datetime
from flask_mail import Mail, Message
from functools import wraps
import requests
import io
import traceback
import pandas as pd
import json
import logging
import secrets
import os

# source ~/.venvs/flask/bin/activate

app = Flask(__name__, template_folder="templates")

# Flask-Mail configuration for Outlook
app.config["MAIL_SERVER"] = "smtp-mail.outlook.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

mail = Mail(app)

logging.basicConfig(
    filename=os.getenv("DIRECTORY_LOG"),
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s",
)

# Configure Flask app settings
app.config["SECRET_KEY"] = secrets.token_hex(16)


# Basic authentication function
def check_auth(username, password):
    # Compare username and password with values from environment variables
    return username == os.getenv("API_USERNAME") and password == os.getenv(
        "API_PASSWORD"
    )


# Authentication decorator
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kws):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            error_response = {"error": "Authentication required"}
            return jsonify(error_response), 400
        return f(
            *args, **kws
        )  # Call the original function with arguments and keyword arguments

    return decorated


@app.errorhandler(Exception)
@requires_auth
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
    traceback_info = [string.replace("^", "") for string in traceback_info]

    response = {"message": error_message, "traceback": traceback_info}

    send_email(response)

    app.logger.error(response)  # Log the error to record.log
    flash("An error occurred")

    error_response = {"error": response}
    return jsonify(error_response), 400


def send_email(response):
    # Establish the SMTP connection
    with app.app_context():
        mail.connect()

        # Create the email message
        msg = Message(
            "There has been an error",
            sender=os.getenv("MAIL_USERNAME"),
            recipients=[os.getenv("MAIL_USERNAME")],
        )
        msg.body = f"{response}"

        # Send the email
        mail.send(msg)


def add_to_session(api_data: dict, data: dict):
    """
    Description:
        Adds info from the API response to the session and stores it in a JSON file.

    Args:
        api_data (dict): API response data.

    Returns:
        None
    """
    for key, value in api_data.items():
        if key == "id" or key in session.get("data", {}):
            continue
        data[key] = value

    if data:
        session["data"] = data  # Store the data in the session

        file_path = os.getenv("FILE_LOG")
        if file_path is None:
            raise ValueError("Error: Environment variable FILE_LOG is not set.")

        existing_data = []

        # Check if the file exists
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as file:
                try:
                    existing_data = json.load(file)
                except json.JSONDecodeError:
                    pass  # Handle invalid JSON content
        else:
            pass  # File doesn't exist, initialize with empty data or defaults

        # Check if the data already exists in the JSON file
        if data not in existing_data:
            # Add new data to the existing data list
            existing_data.append(data)

            # Write the updated data to the file
            with open(file_path, "w", encoding="utf-8") as file:
                # Serialize the updated data to JSON format and write it to the file
                json.dump(existing_data, file, ensure_ascii=False, indent=4)

            print("Data successfully appended to the file.")
        else:
            print("Data already exists in the file. Skipping.")

        response = f"Data fetched and stored in session successfully at {datetime.datetime.now()}"
        app.logger.info(response)


@app.route("/show", methods=["GET", "POST"])
@requires_auth
def show():
    # To load from pickle file
    data = []

    file_path = os.getenv("FILE_LOG")
    if file_path is None:
        raise ValueError("Error: Environment variable FILE_LOG is not set.")

    with open(file_path, encoding="utf-8") as file:
        try:
            data = json.load(file)
        except ValueError:
            error_response = {"error": "Invalid JSON format in the file."}
            return jsonify(error_response), 400

    return jsonify(data)


@app.route("/api/v1/shipments", methods=["GET", "POST"])
@requires_auth
def index():
    data = {}
    api_data = request.get_json()  # Get JSON data from the POST request
    add_to_session(api_data, data)  # Add data to session
    idorder = str(session.get("data", {}).get("picklist", {}).get("idorder"))

    # Get API URL from environment variable
    api_url = os.getenv("PICKER_API_URL")
    # Get the API key from the environment variable
    api_key = os.getenv("PICKER_API_KEY")

    if not api_url or not api_key:
        raise ValueError(
            "The API key, API URL could not be found in the environment or session data."
        )

    api_url = api_url + idorder

    api_url = api_url.replace('"', "")

    # Making a GET request with basic authentication
    response = requests.get(api_url, auth=(api_key, ""))

    if not response.ok:
        error_response = {"error": response.json()}
        return jsonify(error_response), 400

    api_data = response.json()
    add_to_session(api_data, data)  # Update session data

    data = {
        "Customer": {
            "CollectionLocation": os.getenv("COLLECTION_LOCATION"),
            "ContactPerson": os.getenv("CONTACT_PERSON"),
            "CustomerCode": os.getenv("CUSTOMER_CODE"),
            "CustomerNumber": os.getenv("CUSTOMER_NUMBER"),
            "Email": os.getenv("EMAIL"),
            "Name": os.getenv("NAME"),
        },
        "Message": {
            "MessageID": "1",
            "MessageTimeStamp": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "Printertype": "GraphicFile|PDF",
        },
        "Shipments": [
            {
                "Addresses": [
                    {
                        "AddressType": "02",
                        "City": session.get("data", {}).get("invoicecity"),
                        "CompanyName": session.get("data", {}).get("invoicename"),
                        "Countrycode": session.get("data", {}).get("invoicecountry"),
                        "Name": "",
                        "StreetHouseNrExt": session.get("data", {}).get(
                            "invoiceaddress"
                        ),
                        "Zipcode": session.get("data", {}).get("invoicezipcode"),
                    },
                    {
                        "AddressType": "01",
                        "City": session.get("data", {})
                        .get("picklist", {})
                        .get("deliverycity"),
                        "CompanyName": session.get("data", {})
                        .get("picklist", {})
                        .get("deliveryname"),
                        "Countrycode": session.get("data", {})
                        .get("picklist", {})
                        .get("deliverycountry"),
                        "Name": session.get("data", {})
                        .get("picklist", {})
                        .get("deliverycontact"),
                        "StreetHouseNrExt": session.get("data", {})
                        .get("picklist", {})
                        .get("deliveryaddress"),
                        "Zipcode": session.get("data", {})
                        .get("picklist", {})
                        .get("deliveryzipcode"),
                    },
                ],
                "Contacts": [
                    {
                        "ContactType": "01",
                        "Email": session.get("data", {})
                        .get("picklist", {})
                        .get("emailaddress"),
                        "TelNr": session.get("data", {})
                        .get("picklist", {})
                        .get("telephone"),
                    }
                ],
                "Dimension": {"Weight": session.get("data", {}).get("weight")},
                "ProductCodeDelivery": "3085",
                "Reference": session.get("data", {})
                .get("picklist", {})
                .get("picklistid"),
            }
        ],
    }

    # Get the API key from the environment variable
    api_key = os.getenv("POSTNL_API_KEY")
    api_url = os.getenv("POSTNL_API_URL")

    if not api_url or not api_key:
        raise ValueError(
            "The API key, API URL could not be found in the environment or session data."
        )

    # Prepare the headers with the API key if available, or None if not available
    headers = {"Content-Type": "application/json", "apikey": api_key}

    # Make the API request with headers
    response = requests.post(api_url, headers=headers, json=data)

    if not response.ok:
        error_response = {"error": response.json()}
        return jsonify(error_response), 400

    api_data = response.json()

    barcode = api_data["ResponseShipments"][0].get("Barcode")
    labels = api_data["ResponseShipments"][0].get("Labels", [])
    content = labels[0].get("Content") if labels else None

    delivery_info = session.get("data", {}).get("picklist", {})
    deliveryzipcode = delivery_info.get("deliveryzipcode")
    country_code = delivery_info.get("deliverycountry")

    if not all([barcode, content, deliveryzipcode, country_code]):
        raise ValueError(
            f"Missing required data in the API response or session {barcode}, {content}, {deliveryzipcode}, {country_code}."
        )

    return {
        "identifier": barcode,
        "trackingurl": f"https://jouw.postnl.nl/track-and-trace/{barcode}-{country_code}-{deliveryzipcode}",
        "carrier_key": "postnl",
        "label_contents_pdf": content,
    }


@app.route("/api/v1/csv/to/xlsx", methods=["POST"])
@requires_auth
def conversion():
    try:
        # Get the CSV data from the POST request
        csv_data = request.get_json()["csv"]

        # Create a BytesIO buffer to store XLSX file in memory
        xlsx_buffer = io.BytesIO()

        # Convert CSV to XLSX and save it in the BytesIO buffer
        df = pd.read_csv(io.StringIO(csv_data), delimiter=";")
        df.to_excel(xlsx_buffer, sheet_name="Sheet1", index=False, engine="xlsxwriter")

        # Seek to the beginning of the BytesIO buffer
        xlsx_buffer.seek(0)

        # Return the XLSX file as an attachment
        return send_file(
            xlsx_buffer,
            download_name="ALMEC_Pricelist.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except FileNotFoundError as e:
        # Handle exceptions appropriately (e.g., log the error, return error response)
        error_response = {"error": e}
        return jsonify(error_response), 500


if __name__ == "__main__":
    # Run the Flask application
    app.run(debug=True)
