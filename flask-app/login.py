from flask import Flask, render_template, flash, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash
import postgresqlite
import sqlalchemy as sa
import datetime
from forms import *
from flask_mail import Mail, Message
from models import *
import requests
import secrets
import base64
import traceback
import json
import logging



@app.route("/", methods=["GET", "POST"])
def login():
    if form.validate_on_submit():
        username = form.username.data 
        password = form.password.data

        user = User.query.filter_by(name=username).first()

        if user:
            if user.password == password:
                return render_template("dashboard.html")
            
        user = User(name = username, password = generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)

        return render_template("dashboard.html")

    return render_template("login.html", form=form)


    