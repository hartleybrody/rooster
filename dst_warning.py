from app import User, sentry, app


def send_texts():

    users = User.query.all()
    # users = User.query.filter_by(phone="12169738246")
    for user in users:
        if user.is_active:

            current_offset = user.time_zone
            suggested_offset = int(current_offset) - 1

            message = "Don't let daylight savings time mess up your alarm!\n\nYour current timezone offset is %s\n\nIf DST has ended for you, reply with \"TZ: %s\" to update." % (current_offset, suggested_offset)
            try:
                sent = user.send_message(message, "dst_warning")
                if sent:
                    print "sent forecast to %s" % user
                else:
                    print "didn't send forecast to %s" % user
            except Exception as e:
                print e
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
