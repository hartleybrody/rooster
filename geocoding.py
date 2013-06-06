# coding=utf-8

import os
import json
import requests


class GeoCodingClient(object):
    """
        A simple client for Google's GeoCoding API
    """
    def __init__(self):
        super(GeoCodingClient, self).__init__()

    def lookup_zipcode(self, zipcode):

        endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": zipcode,
            "sensor": "false"
        }

        r = requests.post(endpoint, params=params)
        return json.loads(r.text)


if __name__ == "__main__":
    g = GeoCodingClient()
    print g.lookup_zipcode("02139")
