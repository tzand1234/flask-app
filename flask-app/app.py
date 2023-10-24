from flask import *
import postgresqlite
import sqlalchemy as sa
import datetime
from forms import *
from flask_mail import *
from models import *
import requests
import traceback 
import json
import logging
import secrets

app = Flask(__name__, template_folder='templates')

logging.basicConfig(filename='record.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

# aK3LYTlao4weKMFmMlmt3OtqN17u3siLKhDD1JM8l2cO9inQ api key

# Configure Flask app settings
app.config['SECRET_KEY'] = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = postgresqlite.get_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.ethereal.email'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'maude.cronin@ethereal.email'
app.config['MAIL_PASSWORD'] = 'jvdfFNjXEFexHnRDFH'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

@app.errorhandler(Exception)
def internal_server_error(e):
    """
    Description:
        Runs when there is a error. Also adds to the log what the error is.

    Args:
        e (The error): A basic description of the following error

    Returns:
        A json file: Text about the error. Contains a message and the traceback.
    """
    # Log the error with file and line information
    error_message = str(e)

    traceback_info = traceback.format_exc().strip().split("\n")

    traceback_info = [string.replace('^', '') for string in traceback_info]
    
    # Return an error response with JSON including the error message and traceback
    response = {
        "message": error_message,
        "traceback": traceback_info
    }

    # Log the error to record.log
    app.logger.info(response)
    
    # Return the json file with the error
    return jsonify(response), 500

def add_to_session(api_data):
    """
    Description:
        Adds info from response to session.
    """

    # Initialize the database dict
    data = {}

    if response.status_code == 200:
        for key, value in api_data.items():
            if key == "id" or not hasattr(Pick_list, key) or key in data:
                continue
            data[key] = value

        if data:
            session['data'] = data  # Store the data in the session
            
        response = f"Data fetched and stored in session successfully at {datetime.datetime.now()}"
        app.logger.info(response)

    else:
        response = f"API request failed at {datetime.datetime.now()}" 
        # Log the error to record.log
        app.logger.info(response)

def add_to_database():
    """
    Description:
        Adds info from response to Database.    
    """

    # Get info from session
    data = session['data']

    try:
        # Attempt to insert a new record
        query = sa.insert(Pick_list).values(data)
        with db.engine.begin() as dbc:
            dbc.execute(query)

    except Exception as e:
        # Handle unique constraint violation or other exceptions
        # Log the exception or handle it based on your application's requirements

        # Assuming idpicklist is defined somewhere before this try-except block
        # If the record exists, update it with the new data
        query = sa.update(Pick_list).where(Pick_list.idpicklist == idpicklist).values(data)
        with db.engine.begin() as dbc:
            dbc.execute(query)
    
    response = f"Data fetched and stored in database successfully at {datetime.datetime.now()}"
    app.logger.info(response)

@app.route("/shipping/dropshipment", methods=["GET", "POST"])
def index():
    try:
        if request.method == "POST":
            # Get JSON data from the POST request
            api_data = request.get_json()

            # Add data to session and database
            add_to_session(api_data)
            add_to_database()

            if 'data' in session:
                idorder = session['data']['picklist']['idorder']
                api_url = f"https://almec-supplies.picqer.com/api/v1/orders/{idorder}"

                # Make a GET request to the API endpoint
                response = requests.get(api_url)
                
                response.raise_for_status()  # Raise exception for 4xx and 5xx status codes

                # Parse JSON response and add to session and database
                api_data = response.json()
                add_to_session(api_data)
                add_to_database()

                barcode = "3SKRME911535608"
                country_code = "NL"
                zip = "7811JC"

            # Select all records from Pick_list
            query = sa.select(Pick_list)

            # Execute the query using SQLAlchemy
            with db.engine.begin() as dbc:
                result = dbc.execute(query)
        else:
            raise ValueError("Invalid request method")

    except requests.exceptions.HTTPError as err:
        # Handle HTTP errors from the API request
        return internal_server_error(f"API Error: {err}")
    except Exception as e:
        # Handle other exceptions
        return internal_server_error(e)

    return render_template('blog/dashboard.html', api_data_list=result)

@app.route('/')
def test():
    return render_template('blog/dashboard.html')

# Create tables based on the Model classes above.
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True, host='0.0.0.0')
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
