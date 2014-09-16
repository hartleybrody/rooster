import os

from app import User, sentry, app, db

def send_texts():

    # users = User.query.filter_by(phone=os.environ["TEST_PHONE_NUM"])
    users = User.query.filter_by(is_active=True)
    for user in users:
        if user.is_active:
            message = "We haven't heard from you in a while, so we're temporarily deactivating your Rooster App account.\n\nReply 'START' to reactivate."
            try:
                sent = user.send_message(message, "deactivation")
                if sent:
                    print "sent request to %s" % user
                    
                else:
                    print "didn't send request to %s" % user
            except Exception as e:
                print e
                sentry.captureException()

            user.is_active = False
            db.session.add(user)
            db.session.commit()


if __name__ == "__main__":

    send_texts()
