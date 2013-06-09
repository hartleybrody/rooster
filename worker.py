from app import User, sentry


def send_texts():

    users = User.query.all()
    for user in users:
        if user.is_active and user.needs_message_now():
            print "%s needs forecast" % user
            try:
                sent = user.send_message()
                if sent:
                    print "sent forecast to %s" % user
                else:
                    print "didn't send forecast to %s" % user
            except:
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
