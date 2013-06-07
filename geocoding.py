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

    def lookup_location(self, location):

        endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": location,
            "sensor": "false"
        }

        r = requests.post(endpoint, params=params)
        return json.loads(r.text)


if __name__ == "__main__":
    g = GeoCodingClient()
    print g.lookup_location("02139")
