from app import db


class User_has_route(db.Model):
    __tablename__ = 'user_has_route'
    route_id = db.Column(db.Integer, db.ForeignKey('route.route_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    tarif = db.Column(db.String(30))
    currency = db.Column(db.String(10))
    date_object = db.Column(db.DateTime)
    lang = db.Column(db.String(10))
    route = db.relationship("Route", back_populates="users")
    user = db.relationship("User", back_populates="routes")


class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True)
    routes = db.relationship("User_has_route", back_populates="user")

    def __repr__(self):
        return '<Userik %r>' % self.token


class Route(db.Model):
    __tablename__ = 'route'
    route_id = db.Column(db.Integer, primary_key=True)
    route_from = db.Column(db.String(100))
    route_to = db.Column(db.String(100))
    date_time = db.Column(db.DateTime)
    free_seats = db.Column(db.Integer)
    last_free_seats = db.Column(db.Integer)
    sent_reminder = db.Column(db.Boolean, default=False)
    users = db.relationship("User_has_route", back_populates="route")

    def __repr__(self):
        return '<Route %r>' % self.date_time


class Station(db.Model):
    __tablename__ = 'station'
    station_id = db.Column(db.Integer, primary_key=True)
    station_title = db.Column(db.String(100))
    station_latitude = db.Column(db.String(100))
    station_longitude = db.Column(db.String(100))
    station_countryCode = db.Column(db.String(100))
    station_priority = db.Column(db.Integer)

    def __repr__(self):
        return '<Station %r>' % self.station_title
