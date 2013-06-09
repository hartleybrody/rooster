import os
import re
import sys
import logging
from datetime import datetime, time

from flask import Flask, render_template, request, redirect, url_for, flash
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from raven.contrib.flask import Sentry

from twilio import TwilioClient
from forecast import ForecastClient
from geocoding import GeoCodingClient

app = Flask(__name__)
app.secret_key = os.urandom(24)

# config postgres
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRES_URL']
db = SQLAlchemy(app)

# config sentry
app.config['SENTRY_DSN'] = os.environ['SENTRY_DSN']
sentry = Sentry(app)

# config logging
l = logging.StreamHandler(sys.stdout)
l.setLevel(logging.DEBUG)
app.logger.addHandler(l)

print "test print test"


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        data = {
            "phone": re.sub("[^\d.]", "", request.form.get("phone", "")),
            "location": request.form.get("location"),
            "alarm_hour": request.form.get("alarm-hour"),
            "alarm_minute": request.form.get("alarm-minute"),
            "alarm_meridian": request.form.get("alarm-meridian"),
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
            flash("Cock-a-doodle-doo! You'll get your first text at %s:%s %s tomorrow..." % (data["alarm_hour"], data["alarm_minute"], data["alarm_meridian"]), "success")
        except IntegrityError:
            try:
                User.query.filter_by(phone=u.phone)
                flash("Hey thanks! Looks like you already signed up.", "warning")
            except:
                flash("Uh oh! Error saving you to the database", "error")
                print "unknown error..."

        return redirect(url_for('homepage'))

    elif request.method == 'GET':
        if "herokuapp.com" in request.url:
            return redirect("http://www.roosterapp.co/"), 301
        else:
            return render_template("homepage.html")


@app.route("/message/receive/", methods=['GET', 'POST'])
def process_inbound_message():

    print "incoming message"
    print request.form

    message_number = re.sub("[^\d.]", "", request.form.get("From", ""))
    message_body = request.form.get("Body").strip().lower()

    print "from %s" % message_number
    print message_body

    actions_performed = []
    errors_encountered = []

    user = User.query.filter(User.phone == message_number).first()
    t = TwilioClient()

    if user is None:
        message = "Couldn't find %s in our system. Go to http://www.roosterapp.co to sign up!" % (message_number)
        t.send_message(to=message_number, message=message)
        return message

    reactivate_keywords = ["start", "yes"]
    for word in reactivate_keywords:
        if word in message_body:
            user.is_active = True
            actions_performed.append("reactivated your account")

    deactivate_keywords = ["stop", "block", "cancel", "unsubscribe", "quit"]
    for word in deactivate_keywords:
        if word in message_body:
            user.is_active = False
            actions_performed.append("deactivated your account")

    if "location:" in message_body:
        location = message_body.split("location:")[1].strip()
        user.location = location
        user.latitude = ""
        user.longitude = ""
        actions_performed.append("updated location to %s" % location)

    if "time:" in message_body:
        time = message_body.split("time:")[1].strip()

        try:
            hour, minute, meridian, timezone = pase_time(time)
            user.alarm_hour = hour
            user.alarm_minute = minute
            user.alarm_meridian = meridian
            user.time_zone = timezone
            actions_performed.append("updated wake up time to %s" % time)
        except Exception as e:
            errors_encountered.append(e)

    if errors_encountered:
        message = "Uh oh!", ", ".join(errors_encountered)

    elif actions_performed:
        db.session.add(user)
        db.session.commit()
        message = "Successfully", ", ".join(actions_performed)

    else:
        message = "We couldn't understand your request."

    print message
    user.send_message(message)
    return message


def pase_time(t):
    # must be in format HH:MM TZ and minute must be a multiple of 15
    t.strip()
    try:
        time, time_zone = t.split(" ")
    except:
        raise Exception("That date format is invalid. It should be HH:MM TZ")

    try:
        parsed_time_zone = int(time_zone)
        assert parsed_time_zone in range(-10, 13)
    except:
        raise Exception("The timezone you sent (%s) appears to be invalid." % time_zone)

    try:
        hour, minute = time.split(":")
        parsed_hour = int(hour)
        parsed_minute = int(minute)
        assert parsed_hour in range(0, 24)
    except:
        raise Exception("The time you sent (%s) appears to be invalid" % time)

    try:
        assert minute in ["00", "15", "30", "45"]
    except:
        raise Exception("The minutes must be either '00', '15', '30', '45', not %s" % minute)

    if parsed_hour > 12:
        meridian = "pm"
        parsed_hour = parsed_hour - 12
    else:
        meridian = "am"

    return hour, minute, meridian, time_zone

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


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # Models # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


class User(db.Model):

    __tablename__ = "rooster_users"

    id =                db.Column(db.Integer, primary_key=True)
    phone =             db.Column(db.String(30), unique=True)
    is_active =         db.Column(db.Boolean, default=True)

    alarm_hour =        db.Column(db.String(2))
    alarm_minute =      db.Column(db.String(2))
    alarm_meridian =    db.Column(db.String(2))
    time_zone =         db.Column(db.String(3))

    location =          db.Column(db.String(64))
    latitude =          db.Column(db.String(24), default="")
    longitude =         db.Column(db.String(24), default="")

    def __init__(self, phone, location, alarm_hour, alarm_minute, alarm_meridian, time_zone):
        self.phone = phone
        self.location = location
        self.alarm_hour = alarm_hour
        self.alarm_minute = alarm_minute
        self.alarm_meridian = alarm_meridian
        self.time_zone = time_zone

    def __repr__(self):
        return '<User %r>' % self.phone

    def needs_message_now(self):
        """
        Should we text the user right now?
        """

        utc_now = datetime.utcnow()
        if utc_now.weekday() in [5, 6]:
            return False  # don't send on weekends

        # get the current number of seconds since the beginning of the day in UTC
        midnight_utc = datetime.combine(utc_now.date(), time(0))
        delta = utc_now - midnight_utc

        current_utc_offset_seconds = int(delta.total_seconds())
        current_utc_offset_hours = current_utc_offset_seconds / (60 * 60)
        current_utc_offset_minutes = (current_utc_offset_seconds - (60 * 60 * current_utc_offset_hours)) / 60

        # figure out the hour they wanted to wake up
        alarm_hour = int(self.alarm_hour)
        if self.alarm_meridian.lower() == "pm":
            alarm_hour += 12

        # shift the hour for their timezone
        time_zone = self.time_zone
        if time_zone.startswith("-"):
            desired_alarm_hour = alarm_hour + int(time_zone.split("-")[1])
        else:
            desired_alarm_hour = alarm_hour - int(time_zone)

        # make sure we don't have any impossible hours
        if desired_alarm_hour > 23:
            desired_alarm_hour -= 24
        elif desired_alarm_hour < 0:
            desired_alarm_hour += 24

        if desired_alarm_hour != current_utc_offset_hours:
            return False

        # allow a bit of variance in the minutes
        minutes_range = range(current_utc_offset_minutes - 10, current_utc_offset_minutes + 10)
        minutes_range = map(wrap_minutes, minutes_range)

        if self.alarm_minute in minutes_range:
            return True
        else:
            return False

    def send_message(self, message):
        t = TwilioClient
        t.send_message(to=self.phone, message=message)

    def send_forecast(self):
        """
        Send this user their forecast
        """

        # ensure we didn't already text this person today
        today = datetime.utcnow().date()
        texts = Text.query.filter(Text.user_id == self.id).all()
        for text in texts:
            if text.sent.date() == today:
                return False

        if self.latitude == "" or self.longitude == "":

            g = GeoCodingClient()
            geo_info = g.lookup_location(self.location)

            latitude = geo_info["results"][0]["geometry"]["location"]["lat"]
            longitude = geo_info["results"][0]["geometry"]["location"]["lng"]

            # save this lat/lon info so we don't need to look up each time
            self.latitude = latitude
            self.longitude = longitude
            db.session.add(self)

        else:
            latitude = self.latitude
            longitude = self.longitude

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
