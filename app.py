import os
from datetime import datetime, time

from flask import Flask, render_template, request, redirect, url_for, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
app.secret_key = os.urandom(24)
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


@app.route("/send/")
def send_texts():

    # get the current number of seconds since the beginning of the day in UTC
    utc_now = datetime.utcnow()
    midnight_utc = datetime.combine(utc_now.date(), time(0))
    delta = utc_now - midnight_utc

    current_utc_offset_seconds = int(delta.total_seconds())
    current_utc_offset_hours = current_utc_offset_seconds / (60 * 60)
    current_utc_offset_minutes = (current_utc_offset_seconds - (60 * 60 * current_utc_offset_hours)) / 60

    return_str = "current UTC time is {h}:{m}\n".format(h=current_utc_offset_hours, m=current_utc_offset_minutes)

    users = User.query.all()
    for user in users:
        alarm_hour = int(user.alarm_hour)
        time_zone = user.time_zone

        if time_zone.startswith("-"):
            desired_alarm_hour = alarm_hour + int(time_zone.split("-")[1])
        else:
            desired_alarm_hour = alarm_hour - int(time_zone)

        if desired_alarm_hour != current_utc_offset_hours:
            continue

        # allow a bit of variance in the minutes
        minutes_range = range(current_utc_offset_minutes - 3, current_utc_offset_minutes + 3)
        minutes_range = map(wrap_minutes, minutes_range)

        if user.alarm_minute not in minutes_range:
            continue

        user.send_message()

    return return_str


def wrap_minutes(m):
    """
    Make sure the minutes in minutes_range stay between 0 and 59.
    """
    if m < 0:
        return m + 60
    elif m > 59:
        return m - 60
    else:
        return m


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
        return '<User %r>' % self.phone

    def send_message(self):
        """
        Send this user their forecast
        """

        today = datetime.utcnow().date()
        texts = Text.query.filter(Text.user_id == self.id).all()

        for text in texts:
            if text.sent.date() == today:
                print "already texted this user today"
                return False

        from geocoding import GeoCodingClient
        from twilio import TwilioClient
        from forecast import ForecastClient

        g = GeoCodingClient()
        geo_info = g.lookup_zipcode(self.zipcode)

        latitude = geo_info["results"][0]["geometry"]["location"]["lat"]
        longitude = geo_info["results"][0]["geometry"]["location"]["lng"]

        f = ForecastClient()
        forecast = f.get_forecast(latitude, longitude)

        t = TwilioClient()
        t.send_message(self.phone, forecast)

        text = Text(user=self, message=forecast)
        db.session.add(text)
        db.session.commit()
        return True


class Text(db.Model):

    __tablename__ = "rooster_texts"

    id =        db.Column(db.Integer, primary_key=True)
    user_id =   db.Column(db.Integer, db.ForeignKey('rooster_users.id'))
    user =      db.relationship('User', backref=db.backref('texts', lazy='dynamic'))
    sent =      db.Column(db.DateTime)
    message =   db.Column(db.String(160))

    def __init__(self, user, message):
        self.user = user
        self.sent = datetime.utcnow()
        self.message = message

    def __repr__(self):
        return '<Text %r>' % self.message


if __name__ == "__main__":
    app.debug = True
    app.run()
