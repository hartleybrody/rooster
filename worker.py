from app import User, sentry, app


def send_texts():

    users = User.query.all()
    for user in users:
        print
        print user.is_active
        print user.needs_message_now()
        if user.is_active and user.needs_message_now():
            print "%s needs forecast" % user
            try:
                sent = user.send_forecast()
                if sent:
                    print "sent forecast to %s" % user
                else:
                    print "didn't send forecast to %s" % user
            except Exception as e:
                print e
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
