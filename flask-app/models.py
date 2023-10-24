import flask_sqlalchemy

db = flask_sqlalchemy.SQLAlchemy()


# class User(UserMixin, db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(64), unique=True, index=True)
#     username = db.Column(db.String(64), unique=True)
#     password_hash = db.Column(db.String(128))

#     @password.setter
#     def password(self, password):
#         self.password_hash = generate_password_hash(password)

#     def verify_password(self, password):
#         return check_password_hash(self.password_hash, password)


class Pick_list(db.Model):
    __tablename__ = 'pick_list'
    
    id = db.Column(db.Integer, primary_key=True)
    idpicklist = db.Column(db.Integer, unique=True, nullable=False)
    picklist = db.Column(db.JSON)
    sender = db.Column(db.JSON)
    recipient = db.Column(db.JSON)
    user = db.Column(db.JSON)

    def to_dict(self):
        return {
            'picklist': self.picklist,
            'recipient': self.recipient,
            'user': self.user,
        }