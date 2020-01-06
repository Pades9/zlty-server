class Ride(object):

    def __init__(self, departure, arrival, seats, price, ride_type, station_from, station_to, tarif, saved):
        super(Ride, self).__init__()
        self.departure = departure
        self.arrival = arrival
        self.seats = seats
        self.price = price
        self.ride_type = ride_type
        self.stationFrom = station_from
        self.stationTo = station_to
        self.tarif = tarif
        self.saved = saved
