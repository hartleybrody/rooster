from app import User, sentry, app


def send_texts():

    users = User.query.all()
    for user in users:
        if user.is_active and user.needs_message_now():
            try:
                print user.send_message()
            except:
                sentry.captureException()


if __name__ == "__main__":

    send_texts()
