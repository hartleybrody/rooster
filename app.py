import os
import re
import sys
import json
import logging
from datetime import datetime, time, timedelta

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


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':

        print "new signup"
        print json.dumps(request.form)

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
            if key == "phone" and len(value) < 10:
                flash("'%s' is too short to be a phone number. Make sure you include the country code." % value, "error")
                return redirect(url_for('homepage'))
            if key == "location" and len(value) < 5:
                flash("You'll need to be more specific about your location. '%s' isn't much to work with." % value, "error")
                return redirect(url_for('homepage'))

        u = User(**data)
        db.session.add(u)

        try:  # validate the number by sending to it
            u.send_message(
                "Thanks for signing up with Rooster App! Your forecasts will be delivered at {hr}:{min}{mer} Mon-Fri. Reply 'STOP' to pause messages, 'OPTIONS' to change settings.".format(
                    hr=u.alarm_hour,
                    min=u.alarm_minute,
                    mer=u.alarm_meridian
                ),
                "welcome"
            )
        except:
            flash("Hmm, we're having trouble sending to that phone number. Make sure you include your country code.", "error")
            return redirect(url_for('homepage'))

        try:  # data has validated, now try saving to DB
            db.session.commit()
            flash("Cock-a-doodle-doo! You should get a confirmation text in a few seconds.", "success")
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

    if request.method == "GET":
        return "Send me messages! http://www.twilio.com/help/faq/sms"

    print "incoming message"

    message_number = re.sub("[^\d.]", "", request.form.get("From", ""))
    message_body = request.form.get("Body").strip()

    print "from %s" % message_number
    print message_body

    actions_performed = []
    errors_encountered = []

    user = User.query.filter(User.phone == message_number).first()

    if user is None:

        if message_number.startswith("1"):  # see if an american forgot to sign up w their country code
            user = User.query.filter(User.phone == message_number[1:]).first()

        if user is None:
            t = TwilioClient()
            message = "Couldn't find %s in our system. Go to http://www.roosterapp.co to sign up!" % (message_number)
            t.send_message(to=message_number, message=message)
            return message

    # reactivate account
    reactivate_keywords = ["start", "yes"]
    for word in reactivate_keywords:
        if word in message_body.lower():
            user.is_active = True
            actions_performed.append("reactivated your account. Welcome back!")

    # deactivate account
    deactivate_keywords = ["stop", "block", "cancel", "unsubscribe", "quit"]
    for word in deactivate_keywords:
        if word in message_body.lower():
            user.is_active = False
            actions_performed.append("deactivated your account. Send 'START' to reactive.")

    # update location
    location_index = message_body.lower().find("location:")
    if location_index != -1:
        location_offset = location_index + len("location:")
        location = message_body[location_offset:].strip()
        user.location = location
        user.latitude = ""
        user.longitude = ""
        user.is_active = True
        actions_performed.append("updated location to %s" % location)

    # update wake up time
    time_index = message_body.lower().find("time:")
    if time_index != -1:
        time_offset = time_index + len("time:")
        time = message_body[time_offset:].strip()

        try:
            hour, minute, meridian = parse_time(time)
            user.alarm_hour = hour
            user.alarm_minute = minute
            user.alarm_meridian = meridian
            user.is_active = True
            actions_performed.append("updated wake up time to %s" % time)
        except Exception as e:
            errors_encountered.append(str(e))

    # update timezone
    timezone_index = message_body.lower().find("tz:")
    if timezone_index != -1:
        timezone_offset = timezone_index + len("tz:")
        timezone = message_body[timezone_offset:].strip()

        try:
            assert int(timezone) in range(-11, 13)
            user.time_zone = timezone
            user.is_active = True
            actions_performed.append("updated time zone to %s" % timezone)
        except:
            errors_encountered.append("timezone %s appears to be invalid" % timezone)

    # see what happened
    if errors_encountered:
        message = "Uh oh! " + ", ".join(errors_encountered)

    elif actions_performed:
        db.session.add(user)
        db.session.commit()
        message = "Successfully " + ", ".join(actions_performed)

    elif "status" in message_body.lower():
        message = "Current account status:\nACTIVE: {is_active}\nLOCATION: {location}\nTIME: {hour}:{minute}{meridian}\nTZ:{timezone}".format(
            is_active=user.is_active,
            location=user.location,
            hour=user.alarm_hour,
            minute=user.alarm_minute,
            meridian=user.alarm_meridian,
            timezone=user.time_zone
        )

    else:
        message = "Reply w:\n'LOCATION:' with a town or region\n'TIME:' formatted HH:MM (in 24hr format)\n'TZ:' timezone offset, ie -4\n'STOP' to stop\n'STATUS' for current acct info"

    print message
    user.send_message(message, "response")
    return message


def parse_time(t):
    # must be in format HH:MM and minute must be a multiple of 15
    time = t.strip()

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

    return hour, minute, meridian


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

    created_on =        db.Column(db.DateTime, default=db.func.now())

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

        # build a datetime object representing their desired wakeup time in UTC
        today = datetime.today()
        todays_desired_alarm_time = datetime(
            hour=desired_alarm_hour,
            minute=int(self.alarm_minute),
            year=today.year,
            month=today.month,
            day=today.day
        )

        margin_of_error = timedelta(seconds=60*8)  # 8 minutes in either direction (16m window total)
        if utc_now - margin_of_error < todays_desired_alarm_time < utc_now + margin_of_error:
            return True

    def send_message(self, message, category):
        """
        An method to send a message to this user.
        """
        t = TwilioClient()
        t.send_message(to=self.phone, message=message)

        text = Text(user=self, message=message, category=category)
        db.session.add(text)
        db.session.commit()

    def send_forecast(self):
        """
        Send this user their forecast
        """

        # ensure we didn't already text this person today
        today = datetime.utcnow().date()
        texts = Text.query.filter(Text.user_id == self.id).all()
        for text in texts:
            if text.category == "forecast" and text.sent.date() == today:
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

        self.send_message(forecast, "forecast")

        return True


class Text(db.Model):

    __tablename__ = "rooster_texts"

    id =        db.Column(db.Integer, primary_key=True)
    user_id =   db.Column(db.Integer, db.ForeignKey('rooster_users.id'))
    user =      db.relationship('User', backref=db.backref('texts', lazy='dynamic'))
    sent =      db.Column(db.DateTime)
    message =   db.Column(db.String(160))
    category =  db.Column(db.String(32))

    def __init__(self, user, message, category):
        self.user = user
        self.sent = datetime.utcnow()
        self.message = message
        self.category = category

    def __repr__(self):
        return '<Text %r>' % self.message


if __name__ == "__main__":
    app.debug = True
    app.run()
