from app import User, sentry, app


def send_texts():

    users = User.query.all()
    for user in users:
        if user.is_active and user.needs_message_now():
            app.logger.debug("%s needs forecast" % user)
            try:
                sent = user.send_message()
                if sent:
                    app.logger.debug("sent forecast to %s" % user)
                else:
                    app.logger.debug("didn't send forecast to %s" % user)
            except:
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
