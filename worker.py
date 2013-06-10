from app import User, sentry, app


def send_texts():

    users = User.query.all()
    for user in users:
        print
        if user.is_active and user.needs_message_now():
            app.logger.info("%s needs forecast" % user)
            try:
                sent = user.send_forecast()
                if sent:
                    app.logger.info("sent forecast to %s" % user)
                else:
                    app.logger.info("didn't send forecast to %s" % user)
            except Exception as e:
                print e
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
