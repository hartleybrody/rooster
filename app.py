import os
from datetime import datetime, time

from flask import Flask, render_template, request, redirect, url_for, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
db = SQLAlchemy(app)


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        data = {
            "phone": request.form.get("phone"),
            "zipcode": request.form.get("zipcode"),
            "alarm_hour": request.form.get("alarm-hour"),
            "alarm_minute": request.form.get("alarm-minute"),
            "time_zone": request.form.get("time-zone"),
        }

        for key, value in data.items():
            if value is None or value == "":
                flash("Whoops, don't forget to fill out %s" % key, "error")
                return redirect(url_for('homepage'))

        u = User(**data)
        db.session.add(u)

        try:
            db.session.commit()
            flash("Cock-a-doodle-doo! You'll get your first text at %s:%s" % (data["alarm_hour"], data["alarm_minute"]), "success")
        except IntegrityError:
            try:
                User.query.filter_by(phone=u.phone)
                flash("Hey thanks! Looks like you already signed up.", "warning")
            except:
                flash("Uh oh! Error saving you to the database", "error")
                print "unknown error..."

        return redirect(url_for('homepage'))

    else:
        return render_template("homepage.html")


class User(db.Model):

    __tablename__ = "rooster_users"

    id =            db.Column(db.Integer, primary_key=True)
    phone =         db.Column(db.String(30), unique=True)
    zipcode =       db.Column(db.String(8))
    alarm_hour =    db.Column(db.String(2))
    alarm_minute =  db.Column(db.String(2))
    time_zone =     db.Column(db.String(3))

    def __init__(self, phone, zipcode, alarm_hour, alarm_minute, time_zone):
        self.phone = phone
        self.zipcode = zipcode
        self.alarm_hour = alarm_hour
        self.alarm_minute = alarm_minute
        self.time_zone = time_zone

    def __repr__(self):
        return '<Phone Num %r>' % self.phone

if __name__ == "__main__":
    app.debug = True
    app.secret_key = os.urandom(24)
    app.run()
