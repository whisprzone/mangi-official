from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from geopy.geocoders import Nominatim
import random, os, json, omdb, re, socket, openrouteservice, geocoder, math, urllib

#TODO:
#get api call to return json in python then translate into jinja/js
#finish consumer things
#submit

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = '08bc1b516a11043a597225cd5572c240'
geolocator = Nominatim(user_agent = "app")

if os.getenv("DATABASE_URL") != None:
    engine = create_engine(os.getenv("DATABASE_URL"))
else:
    engine = create_engine("postgres://dzigpqzoyzzhfq:c379ba3827c9d99b15caac323f3d2e17a695e835b93a8fac174b7de9d8c15bd0@ec2-54-225-106-93.compute-1.amazonaws.com:5432/des33f58ules9j")

client = openrouteservice.Client(key = '5b3ce3597851110001cf6248065eabf9d1e1454bbef78fe96f3016ec')
db = scoped_session(sessionmaker(bind = engine))

@app.route('/', methods = ['GET', 'POST'])
def index():
    return render_template("home.html", signed_in = True)

@app.route('/logout')
def logout():
    session.pop("username")
    return redirect(url_for("index"))

@app.route('/delivery')
def delivery():
    return render_template("delivery.html")

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get("fullname")
        address = request.form.get("address")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        creditcard = request.form.get("creditcard")
        cvv = request.form.get("cvv")
        expiration = request.form.get("expiration")

        if str(fullname) == '' or str(address) == '' or str(phone) == '' or str(email) == '' or str(password) == '' or str(creditcard) == '' or str(cvv) == '' or str(expiration) == '':
            return render_template("signup.html", error_message = "Please ensure all fields are filled up.")

        else:

            email = str(email)
            arr = []
            for match in re.finditer('@', email):
                arr.append(match)

            if len(arr) == 1:
                check_email = list(db.execute("SELECT email FROM customers WHERE email = :email", {"email": email}))
                if check_email != []:
                    email = ''
                    return render_template("signup.html", error_message = "There is an already an account associated with this email account.")
                else:
                    db.execute("INSERT INTO customers (email, password, address, phone, creditcard, fullname, cvv, expiration) VALUES (:email, :password, :address, :phone, :creditcard, :fullname, :cvv, :expiration)", {"email": str(email), "password": "", "address": "", "phone": 0, "creditcard": 0, "fullname": fullname, "cvv": 0, "expiration": ""})
            else:
                email = []
                return render_template("signup.html", error_message = "Please enter a valid email address.")

            if email != '':
                if len(str(password)) >= 6 and ' ' not in str(password):
                    db.execute("UPDATE customers SET password = :password WHERE email = :email", {"password": str(password), "email": email}) 

                else:
                    return render_template("signup.html", error_message = "Your password needs to be at least 6 characters long and should not contain spaces.")

                if len(str(creditcard)) == 16 and (str(creditcard)[0] == "3" or str(creditcard)[0] == "4" or str(creditcard)[0] == "5" or str(creditcard)[0] == "6"):
                    try:
                        db.execute("UPDATE customers SET creditcard = :creditcard WHERE email = :email", {"creditcard": int(str(creditcard)), "email": email})

                    except ValueError:
                        return render_template("signup.html", error_message = "Please enter a valid credit card number.") 

                else:
                    return render_template("signup.html", error_message = "Please enter a valid credit card number.")

                if len(cvv) == 3:
                    try:
                        db.execute("UPDATE customers SET cvv = :cvv WHERE email = :email", {"cvv": int(str(cvv)), "email": email})

                    except ValueError:
                        return render_template("signup.html", error_message = "Please enter a valid CVV.")

                else:
                    return render_template("signup.html", error_message = "Please enter a valid CVV.")

                try: # because this thing sometimes returns socket timed out errors randomly 
                    location = geolocator.geocode(str(address), timeout = None)
                    lat_long = (location.latitude, location.longitude)

                except GeocoderTimedOut as E: # should work on second try (in my experience)
                    location = geolocator.geocode(str(address))
                    lat_long = (location.latitude, location.longitude)

# warn people not to use postal codes 
# try to handle the error thing
                if location != None and "Singapore" in str(location):
                    db.execute("UPDATE customers SET address = :address WHERE email = :email", {"address": str(lat_long), "email": email})
                    session["address"] = str(location)

                else:
                    return render_template("signup.html", error_message = "Please enter a valid address. Valid addresses include street/road name and a number, like 9 Bishan Place or 1 Raffles Institution Lane. Addresses must be located in Singapore. Do not include postal codes.")

                if len(str(phone)) == 8:
                    try:
                        db.execute("UPDATE customers SET phone = :phone WHERE email = :email", {"phone": int(str(phone)), "email": email})
                    except ValueError:
                        return render_template("signup.html", error_message = "Please enter a valid phone number. Singapore phone numbers contain only 8 digits.")

                else:
                    return render_template("signup.html", error_message = "Please enter a valid phone number. Singapore phone numbers contain only 8 digits.")

                if len(str(expiration)) == 7:
                    try:
                        expiration = str(expiration)
                        arr = expiration.split("/")
                        if len(arr) == 2:
                            try:
                                arr[0] = int(arr[0])
                                arr[1] = int(arr[1])
                                db.execute("UPDATE customers SET expiration = :expiration WHERE email = :email", {"expiration": expiration, "email": email})
                                session["logged_in"] = True
                                return render_template("home.html")
                            except ValueError:
                                return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")
                        else:
                            return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")
                    except:
                        return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")

                else:
                    return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")   
        
    db.commit()
    return render_template("signup.html")
@app.route('/login', methods = ["GET", "POST"])
def login():
    if request.method == 'POST':
        email_phone = request.form.get("email-phone")
        password = request.form.get("password")
               
        try:
            phone = int(email_phone)
            check_user = db.execute("SELECT * FROM customers WHERE phone = :phone AND password = :pass", {"phone": phone, "pass": password})
        except ValueError:  
            check_user = db.execute("SELECT * FROM customers WHERE email = :email AND password = :pass", {"email": str(email_phone), "pass": str(password)}).fetchone()
        
        if check_user == None:
            return render_template("login.html", error_message = "That didn't work. Check the spelling of your username and password, and whether you have created an account at all.")
        else:
            session['logged_in'] = True
            session['fullname'] = check_user["fullname"]
            session['address'] = check_user["address"]
            return redirect(url_for("index"))
        
    return render_template("login.html", error_message = "")

@app.route('/tracker')
def tracker():
    try:
        if session["logged_in"]:
            all_restaurants_names = list(db.execute("SELECT business_name FROM businesses").fetchall())
            all_restaurants = list(db.execute("SELECT address FROM businesses").fetchall())
            empty_arr = []
            origin_coordinates_arr = session["address"].replace("(", "").replace(")", "").split(",")
            origin_coordinates = (float(origin_coordinates_arr[1]), float(origin_coordinates_arr[0]))
            if all_restaurants != []:
                for i in range(0, len(all_restaurants)):
                    lat_long = (float(all_restaurants[i][0].replace("(", "").replace(")", "").split(",")[1]), float(all_restaurants[i][0].replace("(", "").replace(")", "").split(",")[0]))
                    empty_arr.append(lat_long)

            destinations = []
            for i in range(1, len(empty_arr)):
                destinations.append(i)

            reverse_origin_coordinates = str(origin_coordinates_arr[1]) + "," + str(origin_coordinates_arr[0])
            reverse_destination_coordinates = str(list(empty_arr[0])[0]) + "," + str(list(empty_arr[0])[1])
            empty_arr.insert(0, origin_coordinates)
            distance_matrix = openrouteservice.distance_matrix.distance_matrix(client, empty_arr, profile = 'driving-car', sources = 0, destinations = destinations, metrics = ["distance", "duration"])
            restaurantlist = []
            for j in range(0, len(all_restaurants)):
                restaurantlist[0] 
            url = str('https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf6248065eabf9d1e1454bbef78fe96f3016ec&start=' + reverse_origin_coordinates + '&end=' + reverse_destination_coordinates).replace(" ", "")
            with urllib.request.urlopen(url) as url2:
                data = json.loads(url2.read().decode())
            return render_template("tracker.html", all_restaurants = "Distance between you and the restaurant: " + str(math.ceil(distance_matrix['durations'][0][1] / 60)) + " minutes", origin_coordinates = origin_coordinates_arr, data = data, restaurantlist = restaurantlist)

    except KeyError:
        return "That didn't work. Have another go at it."

        

















@app.route('/signup_success', methods = ['POST'])
def signup_success():
    return render_template("signup_success.html")


@app.route('/settings')
def settings():
    return render_template("settings.html")

@app.route('/business_signup', methods = ['GET', 'POST'])
def business_signup():
    if request.method == 'POST':
        business_name = request.form.get("business_name")
        address = request.form.get("address")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        if str(business_name) == '' or str(address) == '' or str(phone) == '' or str(email) == '' or str(password) == '':
            return render_template("business_signup.html", error_message = "Please ensure all fields are filled up.")

        else:

            email = str(email)
            arr = []
            for match in re.finditer('@', email):
                arr.append(match)

            if len(arr) == 1:
                check_email = list(db.execute("SELECT email FROM businesses WHERE email = :email", {"email": email}))
                if check_email != []:
                    email = ''
                    return render_template("business_signup.html", error_message = "There is an already an account associated with this email account.")
                else:
                    session["email"] = email
                    session["logged_in"] = True
                    db.execute("INSERT INTO businesses (business_name, address, phone, email, password) VALUES (:business_name, :address, :phone, :email, :password)", {"business_name": "", "address": "", "phone": 0, "email": str(email), "password": "",})
            else:
                email = []
                return render_template("businesses_signup.html", error_message = "Please enter a valid email address.")

            if email != '':
                if len(str(password)) >= 6 and ' ' not in str(password):
                    db.execute("UPDATE businesses SET password = :password WHERE email = :email", {"password": str(password), "email": email}) 

                else:
                    return render_template("business_signup.html", error_message = "Your password needs to be at least 6 characters long and should not contain spaces.")
                
                try: # because this thing sometimes returns socket timed out errors randomly 
                    location = geolocator.geocode(str(address), timeout = None)
                    lat_long = (location.latitude, location.longitude)

                except: # should work on second try (in my experience)
                    location = geolocator.geocode(str(address))
                    lat_long = (location.latitude, location.longitude)

# warn people not to use postal codes 
# try to handle the error thing
                if location != None and "Singapore" in str(location):
                    db.execute("UPDATE businesses SET address = :address WHERE email = :email", {"address": str(lat_long), "email": email})

                else:
                    return render_template("business_signup.html", error_message = "Please enter a valid address. Valid addresses include street/road name and a number, like 9 Bishan Place or 1 Raffles Institution Lane. Addresses must be located in Singapore. Do not include postal codes.")

                if len(str(phone)) == 8:
                    try:
                        db.execute("UPDATE businesses SET phone = :phone WHERE email = :email", {"phone": int(str(phone)), "email": email})
                    except ValueError:
                        return render_template("business_signup.html", error_message = "Please enter a valid phone number. Singapore phone numbers contain only 8 digits.")

                else:
                    return render_template("business_signup.html", error_message = "Please enter a valid phone number. Singapore phone numbers contain only 8 digits.")

    db.commit()
    return render_template("business_signup.html")

@app.route('/business_mode')
def business_mode():
    return render_template("business_mode.html")
@app.route('/search', methods = ['POST'])
def search():
    movie = request.form.get("movie").lower()
    
    try:
        year = int(movie) # because I converted year to an integer in import.py
        movies = db.execute("SELECT * FROM movies WHERE year = :year", {"year": year}).fetchall()
        if movies == []:
            return render_template("404error.html")
        return render_template("search_results.html", id = movie, movies = movies)

    except ValueError:

        if movie[0:3] == 'tt':

            movies = db.execute("SELECT * FROM movies WHERE imdb_id = :imdb_id", {"imdb_id": movie}).fetchall()
            if movies == []:
                return render_template("404error.html")
            return render_template("search_results.html", id = movie, movies = list(movies))

        else:
            movies = db.execute("SELECT * FROM movies WHERE title ILIKE :title", {"title": "%" + movie + "%"}).fetchall()

            if movies == []:
               return render_template("404error.html")
 
            return render_template("search_results.html", id = movie, movies = movies)

@app.route('/movie/<string:title>', methods = ["GET", "POST"])

def movie(title):

    output = db.execute("SELECT * FROM movies WHERE title = :title", {"title": title}).fetchone()
    get_reviews = list(db.execute("SELECT reviews FROM movies WHERE title = :title", {"title": title}).fetchone())[0]
    
    if request.method == 'POST':
        review = request.form.get("review")
        rating = str(request.form.get("rating"))

        if review is not '' or rating is not '':
            if len(get_reviews) == 0: # because of the way json.loads() works, we need to have a check to see if reviews exist or not
                review_dictionary = {session['username']: {}}
                try:
                    if session['logged_in']:
                        review_dictionary[session['username']]["review"] = review
                        review_dictionary[session['username']]["rating"] = rating + '/10'
                        reviews_json = json.dumps(review_dictionary)
                        db.execute("UPDATE movies SET reviews = :reviews WHERE title = :title", {"reviews": reviews_json, "title": title})
                        db.commit()
                        test_update = list(db.execute("SELECT reviews FROM movies WHERE title = :title", {"title": title}).fetchone())[0]
                        return render_template("movie.html", movie = output, reviews_present = True, reviews = review_dictionary, error_message = '')
                except KeyError:
                    return render_template("movie.html", movie = output, reviews_present = False, reviews = None, error_message = "You need to be logged in in order to submit a review! Please sign up or login to continue.")
        
            else:
                review_dictionary = json.loads(get_reviews)
                try:
                    if session['logged_in']:
                        review_dictionary[session['username']]["review"] = review
                        review_dictionary[session['username']]["rating"] = rating + '/10'
                        reviews_json = json.dumps(review_dictionary)
                        db.execute("UPDATE movies SET reviews = :reviews WHERE title = :title", {"reviews": reviews_json, "title": title})
                        db.commit()
                        test_update = list(db.execute("SELECT reviews FROM movies WHERE title = :title", {"title": title}).fetchone())[0]
                        return render_template("movie.html", movie = output, reviews_present = True, reviews = review_dictionary, error_message = '')
                except KeyError:
                    return render_template("movie.html", movie = output, reviews_present = True, reviews = review_dictionary, error_message = "You need to be logged in in order to submit a review! Please sign up or login to continue.")

        else:
            if len(get_reviews) == 0:
                return render_template("movie.html", movie = output, reviews_present = False, reviews = None, error_message = 'Please fill in both fields.')
            else:
                return render_template("movie.html", movie = output, reviews_present = True, reviews = json.loads(get_reviews), error_message = 'Please fill in both fields.')


    
    if len(get_reviews) == 0:
        return render_template("movie.html", movie = output, reviews_present = False, reviews = None, error_message = '')

    else:
        return render_template("movie.html", movie = output, reviews_present = True, reviews = json.loads(get_reviews), error_message = '')

@app.route('/api/<string:imdb_id>')
def api(imdb_id):
    res = omdb.imdbid(imdb_id)
    if res != {}:
        dictionary = {"title": res["title"], "year": res["year"], "imdb_id": res["imdb_id"], "director": res["director"], "actors": res["actors"], "imdb_rating": res["imdb_rating"]}
        get_reviews = list(db.execute("SELECT reviews FROM movies WHERE imdb_id = :imdb_id", {"imdb_id": imdb_id}).fetchone())[0]
        if len(get_reviews) == 0:
            dictionary["review_count"] = 0
            dictionary["average_score"] = 0
            return jsonify(dictionary)

        else:
            newdict = json.loads(get_reviews)
            review_count = len(newdict.keys())
            score = 0
            counter = 0
            for key, value in newdict.items():
                rating = int(value["rating"].replace("/10", ''))
                score += rating
                counter += 1
            average_score = float(score / counter)
            dictionary["review_count"] = review_count
            dictionary["average_score"] = average_score
            return jsonify(dictionary)

    else:
        return render_template("404error.html")
