This is a Flask-based API for handling various operations such as shipment data management, error logging, file conversions, and email notifications. It integrates with external APIs for fetching and sending shipment data, and it also provides features for handling CSV-to-XLSX file conversion.

Features
Basic Authentication: Ensures API access is restricted to authorized users.
Error Handling: Logs errors and sends email notifications when issues occur.
Session Management: Stores data fetched from APIs in a session and logs it to a file.
Shipment API: Retrieves and processes shipment information from external APIs.
File Conversion: Converts CSV data to an Excel (XLSX) format.
Email Notification: Sends an email notification when an error occurs.



Prerequisites
Before running this application, make sure you have the following:

Python 3.7 or higher.
Required dependencies (listed below) installed in your Python environment.
Setup
Create a virtual environment:

bash
Copy code
python3 -m venv ~/.venvs/flask
Activate the virtual environment:

bash
Copy code
source ~/.venvs/flask/bin/activate
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Set up environment variables:
Ensure the following environment variables are set:

MAIL_USERNAME – Your Outlook email username.
MAIL_PASSWORD – Your Outlook email password.
API_USERNAME – Username for API authentication.
API_PASSWORD – Password for API authentication.
PICKER_API_URL – API URL for fetching shipment data.
PICKER_API_KEY – API key for fetching shipment data.
POSTNL_API_KEY – API key for PostNL shipment processing.
POSTNL_API_URL – API URL for PostNL shipment processing.
COLLECTION_LOCATION, CONTACT_PERSON, CUSTOMER_CODE, CUSTOMER_NUMBER, EMAIL, NAME – Customer-specific information.
DIRECTORY_LOG – Path to the log file.
FILE_LOG – Path to the JSON file used for session storage.
Routes
POST /api/v1/shipments
This endpoint processes shipment data by making API calls and updating session data.

Request Body:
json
Copy code
{
  "key": "value"
}
Response:
Returns a JSON object containing the shipment details, including tracking URLs and barcode information.

GET /show
This endpoint retrieves all the data stored in the session, loaded from the JSON file.

Response:
Returns the stored session data in JSON format.

POST /api/v1/csv/to/xlsx
Converts CSV data (provided in the request) to an Excel (.xlsx) file.

Request Body:
json
Copy code
{
  "csv": "your,csv,data"
}
Response:
Returns an Excel file (ALMEC_Pricelist.xlsx) containing the converted data.

Error Handling
All errors are logged to a file and an email notification is sent to the configured email address. The application will return an error message in the response when an exception occurs.

Logging
Logs are saved in the file path specified by the DIRECTORY_LOG environment variable. Errors are logged in a detailed format that includes timestamp, error type, and traceback information.

Example of CSV-to-XLSX Conversion
To use the /api/v1/csv/to/xlsx endpoint:

Send a POST request with the CSV data:

json
Copy code
{
  "csv": "name,price\nitem1,10.5\nitem2,20.0"
}
Response: An Excel file (ALMEC_Pricelist.xlsx) will be returned with the data.

Notes
This application assumes that you have access to external APIs such as the Picker API and PostNL API for shipment management.
Ensure that the necessary environment variables are set correctly for email, API access, and file paths.
You can modify the application to handle other file formats or extend the functionality as needed.
