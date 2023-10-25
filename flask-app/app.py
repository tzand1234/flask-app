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
from dotenv import load_dotenv
import os

app = Flask(__name__, template_folder='templates')

load_dotenv()  # Load environment variables from .env file

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

    app.logger.error(response)  # Log the error to record.log
    flash('An error occurred')
    
    return render_template('auth/error.html', error_message=response)

def add_to_session(api_data):
    """
    Description:
        Adds info from the API response to the session and stores it in a JSON file.

    Args:
        api_data (dict): API response data.

    Returns:
        None
    """
    data = {}
    for key, value in api_data.items():
        if key == "id" or key in session.get('data', {}):
            continue
        data[key] = value

    if data:
        session['data'] = data  # Store the data in the session

        with open("Logs/dict.json", "w") as json_file:
            json.dump(data, json_file)  # Write data to JSON file

        response = f"Data fetched and stored in session successfully at {datetime.datetime.now()}"
        app.logger.info(response)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            api_data = request.get_json()  # Get JSON data from the POST request
            add_to_session(api_data)  # Add data to session
            idorder = session.get('data', {}).get('picklist', {}).get('idorder')

            if idorder:
                # Get API URL from environment variable
                api_url = os.getenv("API_URL") + f"{idorder}"
                response = requests.get(api_url)
                api_data = response.json()
                add_to_session(api_data)  # Update session data

            result = session.get('data', {})
            return render_template('blog/dashboard.html', api_data_list=result)

        except Exception as e:
            return internal_server_error(e)  # Handle exceptions

    else:
        return render_template('blog/dashboard.html')

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)
# ----------------------------------------------------------------------------------------

def login():
    """Handles the login page."""
    
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(name=username).first()

        if user:
            if user.password == password:
                return render_template("dashboard.html")
            

        user = User(name=username, password= generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)

        return render_template("dashboard.html")

    return render_template("login.html", form=form)

def fetch_and_send_data():
    """_summary_

    Returns:
        _type_: _description_
    """
    
    try:
        # Replace these values with your own data
        username = session.get('username')
        password = session.get('password')


        # The data you want to send to the endpoint (replace with your own data)
        data = {
            "identifier": "3SAPPL80237480",
            "trackingurl": "https://example.com/shipment/3SAPPL80237480",
            "carrier_key": "postnl",
            "label_contents_pdf": "--BASE64 ENCODED VERSION OF PDF--",
            "label_contents_zpl": "--BASE64 ENCODED VERSION OF ZPL--"
        }

        # Add Basic Auth headers to the request
        headers = {
            "Authorization": f"Basic {base64.b64encode(f'{username}:{password}').decode('utf-8')}",
            "Content-Type": "application/json"  # Adjust this if the API expects a different type
        }

        # Make a POST request to the endpoint with the data and headers
        response = requests.post(api_url, json=data, headers=headers)

        # Check the response status code to see if the request was successful
        if response.status_code == 200:
            flash("The request was successful.")
        else:
            flash("API request failed")

    except Exception as e:
        return internal_server_error(e)

    query = sa.select(Pick_list)
    with db.engine.begin() as dbc:
        result = dbc.execute(query)

    return render_template('index.html', api_data_list=result)

def send_mail(link=None, subject=None, sender=None, recipients=None):

    """
    Send a message to via email.

    Args:
        subject (str): The subject of the email. Defaults to None.
        sender (str): The email of the sender. Defaults to None.
        recipients (str): The email of recipient. Defaults to None.
    """

    msg = Message(
    subject="Your track and trace link.", 
    sender="maude.cronin@ethereal.email", 
    recipients=["maude.cronin@ethereal.email"]
    )

    link = "https://docs.api.postnl.nl/#tag/Shipment/paths/~1shipment~1v2_2~1label/post"
    msg.html = f"Click the following link to see your track and trace: <a href='{link}'>Click here</a>"
    mail.send(msg)

    response = f"Email send successfully at {datetime.datetime.now()}"
    app.logger.info(response)



  
  
  
# # Select all records from Pick_list
# query = sa.select(Pick_list)

# # Execute the query using SQLAlchemy
# with db.engine.begin() as dbc:
#     result = dbc.execute(query)

# response = f"API request failed at {datetime.datetime.now()}" 
# # Log the error to record.log
# app.logger.info(response)


# def add_to_database():
    # """
    # Description:
    #     Adds info from response to Database.    
    # """

    # # Get info from session
    # data = session['data']

    # try:
    #     # Attempt to insert a new record
    #     query = sa.insert(Pick_list).values(data)
    #     with db.engine.begin() as dbc:
    #         dbc.execute(query)

    # except Exception as e:
    #     # Handle unique constraint violation or other exceptions
    #     # Log the exception or handle it based on your application's requirements

    #     # Assuming idpicklist is defined somewhere before this try-except block
    #     # If the record exists, update it with the new data
    #     query = sa.update(Pick_list).where(Pick_list.idpicklist == idpicklist).values(data)
    #     with db.engine.begin() as dbc:
    #         dbc.execute(query)
    
    # response = f"Data fetched and stored in database successfully at {datetime.datetime.now()}"
    # app.logger.info(response)
