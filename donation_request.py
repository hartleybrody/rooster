import os

from app import User, sentry, app


def send_texts():

    # users = User.query.filter_by(phone=os.environ["TEST_PHONE_NUM"])
    users = User.query.filter_by(is_active=True)
    for user in users:
        if user.is_active:

            current_offset = user.time_zone
            suggested_offset = int(current_offset) + 1

            message = "Hope you've found Rooster to be a helpful addition to your morning! The site costs $30/month to operate. I'd love your support: http://www.roosterapp.co/donate/"
            try:
                sent = user.send_message(message, "donation_request")
                if sent:
                    print "sent request to %s" % user
                else:
                    print "didn't send request to %s" % user
            except Exception as e:
                print e
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
