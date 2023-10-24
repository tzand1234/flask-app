import flask_sqlalchemy

db = flask_sqlalchemy.SQLAlchemy()

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