import requests


class Station:
    def __init__(self, id, title, latitude, longitude, country_code, priority):
        super(Station, self).__init__()
        self.id = id
        self.title = title
        self.latitude = latitude
        self.longitude = longitude
        self.countryCode = country_code
        self.priority = priority


class Stations(object):
    _url = "https://www.studentagency.cz/data/wc/ybus-form/destinations-sk.json"

    def __init__(self):
        super(Stations).__init__()
        self.session = requests.Session()

    def fetch_stations(self):
        stations = list()

        request = self.session.post(self._url, headers={'Content-type': 'application/json; charset=utf-8'})
        objects = request.json()

        destinations = objects["destinations"]
        for destination in destinations:
            cities = destination["cities"]
            if destination["code"] == "SK":
                priority = 3
            elif destination["code"] == "CZ":
                priority = 2
            else:
                priority = 1
            for city in cities:
                new_station = Station(str(city["id"]), city["name"], "", "", destination["code"], priority)
                stations.append(new_station.__dict__)
                for station in city["stations"]:
                    new_station = Station(str(station["id"]), city["name"] + " " + station["name"],
                                          str(station["latitude"]), str(station["longitude"]), destination["code"],
                                          priority)
                    stations.append(new_station.__dict__)

        return stations
