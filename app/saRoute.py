import datetime

import requests
import socks
import socket
from bs4 import BeautifulSoup

from app.ride import Ride
from app.models import *


class SaRoute(object):
    _url = "http://jizdenky.studentagency.sk/m/Booking/from/" \
           "{start}/to/{end}/tarif/{tarif}/departure/{departure}/retdep/{retdep}/return/{ret}/credit/{credit}"

    def __init__(self, start, end, tarif, day, time, credit, currency, user_token):
        super(SaRoute, self).__init__()
        self.start = start
        self.end = end
        self.tarif = tarif
        self.day = day
        self.time = time
        self.credit = credit
        self.currency = currency
        self.user_token = user_token

        self.session = requests.Session()

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        self._end = end

    @property
    def tarif(self):
        return self._tarif

    @tarif.setter
    def tarif(self, tarif):
        self._tarif = tarif

    @property
    def currency(self):
        return self._currency

    @currency.setter
    def currency(self, currency):
        self._currency = currency

    @property
    def user_token(self):
        return self._user_token

    @user_token.setter
    def user_token(self, user_token):
        self._user_token = user_token

    @property
    def day(self):
        return self._day

    @day.setter
    def day(self, day):
        self._day = day

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, time):
        self._time = time

    @property
    def credit(self):
        return self._credit

    @credit.setter
    def credit(self, credit):
        self._credit = credit

    def fetch_rides(self):

        # SET PROXY, default disabled
        # socks.setdefaultproxy(proxy_type=socks.PROXY_TYPE_SOCKS5, addr="127.0.0.1", port=9050)
        # socket.socket = socks.socksocket

        if not (self.start and self.end and self.tarif and self.day and self.credit):
            return

        url = self._url.format(
            start=self.start,
            end=self.end,
            tarif=self.tarif,
            departure=self.day,
            retdep=self.day,
            ret=False,
            credit=self.credit
        )
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.2; rv:20.0) Gecko/20121202 Firefox/20.0'}
        cookie = {'mobileCurrency': self.currency}
        request = self.session.post(url, headers=headers, cookies=cookie)
        bs = BeautifulSoup(request.text, "html.parser")
        if not bs.find("div", "detail-tabs"):
            return False

        day_parse = bs.find("div", "daySeparator").text.split()
        day_format = datetime.datetime.strptime(day_parse[1], '%d.%m.%y').date()
        day_string = day_format.strftime("%Y%m%d")
        day_string_db = day_format.strftime("%d/%m/%Y")
        if day_string != self.day:
            return False

        linesRaw = bs.find("div", "detail-tabs").find_all("div", "line")
        rides = list()
        for lineRaw in linesRaw:

            ride_type = lineRaw.find("span", "type-img").img.get("title")
            departure = lineRaw.find("span", "departure").text
            arrival = lineRaw.find("span", "arrival").text
            seats = lineRaw.find("span", "free").text
            price = lineRaw.find("span", "price").text

            saved = False
            date_time = day_string_db + "-" + departure
            date_object = datetime.datetime.strptime(date_time, '%d/%m/%Y-%H:%M')
            route = Route.query.filter_by(route_from=self.start, route_to=self.end,
                                          date_time=date_object).first()
            user = User.query.filter_by(token=self.user_token).first()

            if route and user:
                user_route = User_has_route.query.filter_by(user_id=user.user_id, route_id=route.route_id).first()
                if user_route:
                    saved = True

            ride = Ride(departure, arrival, seats, price, ride_type, self.start, self.end, self.tarif, saved)
            rides.append(ride.__dict__)

        return rides

    def fetch_ride(self):
        rides = self.fetch_rides()
        if rides:
            for i in range(0, len(rides)):
                if len(rides[i]['departure']) == 4:
                    rides[i]['departure'] = "0" + rides[i]['departure']
                if self.time == rides[i]['departure']:
                    return rides[i]
        return False
