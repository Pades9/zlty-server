import datetime
import json

from flask import request, render_template

from app import app, db, models, clientapns, clientgcm
from app.pushToken import PushToken
from app.saRoute import SaRoute
from app.stations import Stations


@app.route('/')
def show_all():
    return render_template('hello.html')


@app.route(
    '/api/routes/from/<from_station>/to/<to_station>/tarif/<tarif>/date/<date>/currency/<currency>/user_token/<user_token>',
    methods=['GET'])
def routes(from_station, to_station, tarif, date, currency, user_token):
    """Return routes according to query parameters"""
    sa = SaRoute(from_station, to_station, tarif, date, False, True, currency, user_token)
    rides = sa.fetch_rides()
    if rides is False:
        return 'Nenasiel sa spoj', 300

    return json.dumps(rides)


@app.route('/api/newTrackingRoute', methods=['POST'])
def new_tracking_route():
    """Save new user route: parameters: dateTime = 24/09/2016-14:00, fromStation, toStation, freeSeats, userToken, lang, tarif, currency """
    if request.method == 'POST':
        date_object = datetime.datetime.strptime(request.form['dateTime'], '%d/%m/%Y-%H:%M')  # example 24/09/2016-14:00
        db_route = _get_route(request.form['fromStation'], request.form['toStation'], date_object,
                              request.form['freeSeats'])

        if db_route.free_seats != "0":
            db_route.last_free_seats = db_route.free_seats
            db_route.free_seats = request.form['freeSeats']
        user = _get_user(request.form['userToken'])

        user_existed_route = models.User_has_route.query.filter_by(user_id=user.user_id,
                                                                   route_id=db_route.route_id).first()
        if user_existed_route:
            db.session.delete(user_existed_route)
            status_code = 201
        else:
            if not request.form['lang']:
                request.form['lang'] = "en"
            user_has_route = models.User_has_route(tarif=request.form['tarif'], currency=request.form['currency'],
                                                   date_object=date_object, lang=request.form['lang'])
            user_has_route.route = db_route
            user_has_route.user = user
            user.routes.append(user_has_route)
            status_code = 200

        db.session.commit()
        db.session.close()

        return '', status_code

    return '', 300


@app.route('/api/userRoutes/<user_token>', methods=['GET'])
def load_user_routes(user_token):
    """Return saved routes for specific user"""
    user = models.User.query.filter_by(token=user_token).first()
    rides = list()
    if user:
        user_routes = models.User_has_route.query.filter(models.User_has_route.user == user).order_by(
            models.User_has_route.date_object)
        for userRoute in user_routes:
            db_route = userRoute.route
            now_timestamp = datetime.datetime.now()
            if db_route.date_time > now_timestamp:
                date_route = db_route.date_time.strftime("%Y%m%d")
                time_route = db_route.date_time.strftime("%H:%M")
                ride = _specific_route(db_route.route_from, db_route.route_to, userRoute.tarif, date_route, time_route,
                                       userRoute.currency)
                if ride:
                    ride['route_id'] = db_route.route_id
                    ride['user_id'] = user.user_id
                    ride['date'] = str(db_route.date_time)
                    ride['currency'] = str(userRoute.currency)
                    rides.append(ride)

    return json.dumps(rides)


def _specific_route(from_station, to_station, tarif, date, time, currency):
    sa = SaRoute(from_station, to_station, tarif, date, time, True, currency, None)
    ride = sa.fetch_ride()
    return ride


@app.route('/api/stations', methods=['GET'])
def load_stations():
    return json.dumps(Stations().fetch_stations(), ensure_ascii=False).encode('utf8')


@app.route('/api/deleteSavedRoute', methods=['POST'])
def delete_saved_route():
    """Delete saved route by user_id and route_id"""
    if request.method == 'POST':
        user_route = models.User_has_route.query.filter_by(user_id=request.form['user_id'],
                                                           route_id=request.form['route_id']).first()
        if user_route:
            db.session.delete(user_route)
            db.session.commit()
            return '', 200

    return '', 300


def _get_user(user_token):
    user = models.User.query.filter_by(token=user_token).first()
    if not user:
        user = models.User(token=user_token)
        db.session.add(user)
    return user


def _get_route(from_station, to_station, date_object, free_seats):
    db_route = models.Route.query.filter_by(route_from=from_station, route_to=to_station, date_time=date_object).first()
    if not db_route:
        db_route = models.Route(route_from=from_station, route_to=to_station, date_time=date_object,
                                free_seats=free_seats)
        db.session.add(db_route)
    return db_route


def _update_free_seats(db_route):
    date_route = db_route.date_time.strftime("%Y%m%d")
    time_route = db_route.date_time.strftime("%H:%M")
    sa_route = SaRoute(db_route.route_from, db_route.route_to, "REGULAR", date_route, time_route, True, "EUR", None)
    ride = sa_route.fetch_ride()
    if ride:
        print(str(db_route.free_seats) + " -" + str(ride['seats']))
        if int(db_route.free_seats) != int(ride['seats']):
            db_route.last_free_seats = db_route.free_seats
            db_route.free_seats = ride['seats']
            return True

    return False


@app.route('/api/route/route_id/<route_id>/user_token/<user_token>', methods=['GET'])
def route(route_id, user_token):
    db_route = models.Route.query.filter_by(route_id=route_id).first()
    user = models.User.query.filter_by(token=user_token).first()
    user_route = models.User_has_route.query.filter_by(user_id=user.user_id, route_id=route_id).first()
    if route:
        date_route = db_route.date_time.strftime("%Y%m%d")
        time_route = db_route.date_time.strftime("%H:%M")
        ride = _specific_route(db_route.route_from, db_route.route_to, user_route.tarif, date_route, time_route,
                               user_route.currency)
        if ride:
            ride['route_id'] = db_route.route_id
            ride['user_id'] = user.user_id
            ride['date'] = str(db_route.date_time)
            ride['currency'] = str(user_route.currency)
            # if int(route.free_seats) != int(ride['seats']) and route.free_seats != "0":
            #     route.last_free_seats = route.free_seats
            #     route.free_seats = ride['seats']
            #     db.session.commit()
            #     db.session.close()
            return json.dumps(ride)

    return 'Nenasiel sa spoj', 300


@app.before_first_request
def _load_local_stations():
    models.Station.query.delete()
    stations = Stations().fetch_stations()
    for station in stations:
        db_station = models.Station(station_id=station['id'], station_title=station['title'],
                                    station_latitude=station['latitude'], station_longitude=station['longitude'],
                                    station_countryCode=station['countryCode'], station_priority=station['priority'])
        db.session.add(db_station)

    db.session.commit()
    return ""


def _send_push(pa_tokens, pa_alert, pa_route_id):
    with app.app_context():
        alert_string = pa_alert
        alert = alert_string.split('#')
        tokens = pa_tokens
        for pushToken in tokens:
            if alert[0] == "0":
                alert = alert[1]
            elif alert[0] == "1":
                if pushToken.lang == "sk":
                    alert = "Uvoľnilo sa jedno miesto. Ponáhľaj sa! " + alert[1]
                elif pushToken.lang == "cz":
                    alert = "Uvolnilo se jedno místo. Pospěš si! " + alert[1]
                else:
                    alert = "It is one released spot. Hurry up! " + alert[1]
            else:
                if pushToken.lang == "sk":
                    alert = "Lístky sa vypredávajú. " + alert[1]
                elif pushToken.lang == "cz":
                    alert = "Lístky se vyprodávají. " + alert[1]
                else:
                    alert = "Tickets will sell off. " + alert[1]

            if len(pushToken.token) == 64:
                res = clientapns.send(pushToken.token, alert, sound="default", badge=1, extra={'route_id': pa_route_id})
                print(res.token_errors)
            else:
                alertAndroid = {'message': alert, 'route_id': pa_route_id}
                res = clientgcm.send(pushToken.token, alertAndroid)
                print(res.responses)

    return True


def first_routes():
    date_object = datetime.datetime.now()
    db_routes = models.Route.query.filter(models.Route.free_seats == "0", models.Route.date_time > date_object)
    for db_route in db_routes:
        user_routes = models.User_has_route.query.filter_by(route_id=db_route.route_id)
        if user_routes and user_routes.count() > 0:
            if _update_free_seats(db_route):
                tokens = list()
                push_route_id = db_route.route_id

                for userRoute in user_routes:
                    user = models.User.query.filter_by(user_id=userRoute.user_id).first()
                    push_token = PushToken(token=user.token, lang=userRoute.lang)
                    tokens.append(push_token)

                db.session.commit()

                if len(tokens) > 0:
                    station_from = models.Station.query.filter_by(station_id=db_route.route_from).first()
                    station_to = models.Station.query.filter_by(station_id=db_route.route_to).first()
                    text_push = "1#" + station_from.station_title + " -> " + station_to.station_title + " (" + db_route.date_time.strftime(
                        "%d/%m/%Y %H:%M") + ")"
                    _send_push(tokens, text_push, push_route_id)

    print("First routes")
    return "First routes"


def second_routes():
    date_object = datetime.datetime.now()
    db_routes = models.Route.query.filter(models.Route.free_seats > "0", models.Route.free_seats <= "15",
                                          models.Route.date_time > date_object)
    for db_route in db_routes:
        user_routes = models.User_has_route.query.filter_by(route_id=db_route.route_id)
        if user_routes and user_routes.count() > 0:
            if _update_free_seats(db_route):
                tokens = list()
                push_route_id = db_route.route_id
                if int(db_route.free_seats) < 10 and db_route.sent_reminder is False:
                    db_route.sent_reminder = True
                    for user_route in user_routes:
                        user = models.User.query.filter_by(user_id=user_route.user_id).first()
                        push_token = PushToken(token=user.token, lang=user_route.lang)
                        tokens.append(push_token)

                if int(db_route.free_seats) > 30 and db_route.sent_reminder is True:
                    db_route.sent_reminder = False

                db.session.commit()

                if len(tokens) > 0:
                    station_from = models.Station.query.filter_by(station_id=db_route.route_from).first()
                    station_to = models.Station.query.filter_by(station_id=db_route.route_to).first()
                    text_push = "2#" + station_from.station_title + " -> " + station_to.station_title + " (" + db_route.date_time.strftime(
                        "%d/%m/%Y %H:%M") + ")"
                    _send_push(tokens, text_push, push_route_id)

    print("Second routes")
    return "Second routes"


def third_routes():
    date_object = datetime.datetime.now()
    db_routes = models.Route.query.filter(models.Route.free_seats > "15", models.Route.date_time > date_object)
    for db_route in db_routes:
        user_routes = models.User_has_route.query.filter_by(route_id=db_route.route_id)
        if user_routes and user_routes.count() > 0:
            if _update_free_seats(db_route):
                tokens = list()
                push_route_id = db_route.route_id
                if int(db_route.free_seats) < 10 and db_route.sent_reminder is False:
                    db_route.sent_reminder = True
                    for userRoute in user_routes:
                        user = models.User.query.filter_by(user_id=userRoute.user_id).first()
                        push_token = PushToken(token=user.token, lang=userRoute.lang)
                        tokens.append(push_token)

                if int(db_route.free_seats) > 30 and db_route.sent_reminder is True:
                    db_route.sent_reminder = False

                db.session.commit()

                if len(tokens) > 0:
                    station_from = models.Station.query.filter_by(station_id=db_route.route_from).first()
                    station_to = models.Station.query.filter_by(station_id=db_route.route_to).first()
                    text_push = "2#" + station_from.station_title + " -> " + station_to.station_title + " (" + db_route.date_time.strftime(
                        "%d/%m/%Y %H:%M") + ")"
                    _send_push(tokens, text_push, push_route_id)

    print("Third routes")
    return "Third routes"
