# coding=utf-8

import os
import json
import requests


class TwilioClient(object):
    """
        A simple client for Twilio's API
    """
    def __init__(self):
        super(TwilioClient, self).__init__()

        self.ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
        self.AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
        self.PHONE_NUM = os.environ["TWILIO_PHONE_NUMBER"]

    def send_message(self, to, message):

        if len(message) > 160:
            raise Exception("Message is too long ({} chars)".format(len(message)))

        endpoint = "https://api.twilio.com/2010-04-01/Accounts/{acct_sid}/SMS/Messages.json".format(acct_sid=self.ACCOUNT_SID)
        data = {
            "From": self.PHONE_NUM,
            "To": to,
            "Body": message
        }

        r = requests.post(endpoint, auth=(self.ACCOUNT_SID, self.AUTH_TOKEN), data=data)
        response = json.loads(r.text)

        if r.status_code not in [200, 201]:
            print response
            raise Exception("Twilio refused the messages: %s" % response.get("message"))

        return response


if __name__ == "__main__":
    t = TwilioClient()
    t.send_message(os.environ["TEST_PHONE_NUM"], "this is a test message")
