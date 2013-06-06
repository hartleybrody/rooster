# coding=utf-8

import os
import sys
import json
import requests
from datetime import datetime


class ForecastClient(object):
    """
        A simple client for Forecast.io's API
    """
    def __init__(self):
        super(ForecastClient, self).__init__()

        self.API_KEY = os.environ["FORECAST_API_KEY"]

    def get_forecast(self, latitude, longitude):

        endpoint = "https://api.forecast.io/forecast/{api_key}/{lat},{lon}".format(api_key=self.API_KEY, lat=latitude, lon=longitude)
        r = requests.get(endpoint)
        return self.interpret_forecast(json.loads(r.text))

    def interpret_forecast(self, forecast):

        overall_summary = ""

        # start with daily summary
        daily_summary = forecast.get("hourly", {}).get("summary", "")
        overall_summary = daily_summary

        if len(overall_summary) > 135:
            return overall_summary  # no room for high temp info

        # add high temp information
        daily_high_temp = -1000
        daily_high_time = None
        for hour in forecast.get("hourly", {}).get("data", [])[:18]:
            hour_temp = hour.get("temperature") or -1000
            if hour_temp > daily_high_temp:
                daily_high_temp = hour_temp
                if hour.get("time"):
                    daily_high_time = datetime.fromtimestamp(hour.get("time"))

        daily_high_hour = daily_high_time.hour
        if daily_high_hour > 12:
            daily_high_hour = daily_high_hour - 12

        temp_summary = "High of {temp} at {hour} o'clock.".format(
            temp=self.format_temperature(daily_high_temp),
            hour=daily_high_hour
        )

        overall_summary = overall_summary + " " + temp_summary

        # add current conditions info
        current_temp = forecast.get("currently", {}).get("temperature", None)
        current_summary = forecast.get("minutely", {}).get("summary", "")

        if current_summary and current_temp and len(overall_summary) < 100:
            overall_summary = "Currently {temp} and will be {summary} {the_rest}".format(
                temp=self.format_temperature(current_temp),
                summary=current_summary.lower(),
                the_rest=overall_summary
            )
        elif current_temp and len(overall_summary) < 145:
            overall_summary = "Currently {temp}. {the_rest}".format(
                temp=self.format_temperature(current_temp),
                the_rest=overall_summary
            )

        return overall_summary

    @staticmethod
    def format_temperature(temp):
        return u"{temp}".format(temp=int(round(temp)))
        # return u"{temp}°".format(temp=int(round(temp)))


if __name__ == "__main__":
    f = ForecastClient()
    print f.get_forecast(42.362481, -71.101771)
