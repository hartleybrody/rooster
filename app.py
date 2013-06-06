import os

from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
db = SQLAlchemy(app)


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        pass
    else:
        return render_template("homepage.html")


class User(db.Model):

    __tablename__ = "rooster_users"

    id =            db.Column(db.Integer, primary_key=True)
    phone =         db.Column(db.String(30), unique=True)
    zipcode =       db.Column(db.String(12))
    alarm_time =    db.Column(db.String(12))
    time_zone =     db.Column(db.String(12))

    def __init__(self, phone, zipcode, alarm_time, time_zone):
        self.phone = phone
        self.zipcode = zipcode
        self.alarm_time = alarm_time
        self.time_zone = time_zone

    def __repr__(self):
        return '<Phone Num %r>' % self.phone

if __name__ == "__main__":
    app.debug = True
    app.run()
