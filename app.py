import os

from flask import Flask, render_template, request, redirect, url_for, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
db = SQLAlchemy(app)


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        u = User(
            phone=request.form.get("phone"),
            zipcode=request.form.get("zipcode"),
            alarm_time=request.form.get("alarm-time"),
            time_zone=request.form.get("time-zone"),
        )
        db.session.add(u)
        try:
            db.session.commit()
            flash("Cock-a-doodle-doo! You'll get your first text at %s" % request.form.get("alarm-time"), "success")
        except IntegrityError:
            try:
                User.query.filter_by(phone=u.phone)
                flash("Hey thanks! Looks like you already signed up.", "warning")
            except:
                flash("Uh oh! Error saving you to the database", "error")

        return redirect(url_for('homepage'))

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
    app.secret_key = os.urandom(24)
    app.run()
