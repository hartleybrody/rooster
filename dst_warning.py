import os

from app import User, sentry, app


def send_texts():

    users = User.query.all(is_active=True)
    # users = User.query.filter_by(phone=os.environ["TEST_PHONE_NUM"])
    for user in users:
        if user.is_active:

            current_offset = user.time_zone
            suggested_offset = int(current_offset) + 1

            message = "Don't let daylight savings time mess up your alarm!\n\nYour current timezone offset is %s\n\nIf DST has started for you, reply with \"TZ: %s\" to update." % (current_offset, suggested_offset)
            try:
                sent = user.send_message(message, "dst_warning")
                if sent:
                    print "sent warning to %s" % user
                else:
                    print "didn't send warning to %s" % user
            except Exception as e:
                print e
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
