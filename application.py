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
    try:
        return render_template("home.html", logged_in = False) 
    except KeyError:
        return render_template("home.html", logged_in = False)

@app.route('/logout')
def logout():
    session["logged_in"] = None
    session["fullname"] = None
    session['address'] = None
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
                    db.execute("INSERT INTO customers (email, password, coordinates, phone, creditcard, fullname, cvv, expiration, main_address) VALUES (:email, :password, :address, :phone, :creditcard, :fullname, :cvv, :expiration, :main_address)", {"email": str(email), "password": "", "address": "", "phone": 0, "creditcard": 0, "fullname": fullname, "cvv": 0, "expiration": "", "main_address": address})
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

                except: # should work on second try (in my experience)
                    location = geolocator.geocode(str(address))
                    lat_long = (location.latitude, location.longitude)

# warn people not to use postal codes 
# try to handle the error thing
                if location != None and "Singapore" in str(location):
                    db.execute("UPDATE customers SET coordinates = :address WHERE email = :email", {"address": str(lat_long), "email": email})
                    session["address"] = str(location)

                else:
                    return render_template("signup.html", error_message = "Please enter a valid address. Addresses must be located in Singapore. Do not include postal codes. Try another address if signup is unsuccessful.")

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
                                session['fullname'] = fullname
                                db.commit()
                                return render_template("home.html")
                            
                            except ValueError:
                                return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")
                        else:
                            return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")
                    except:
                        return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")

                else:
                    return render_template("signup.html", error_message = "Please enter a valid expiration date, in the form MM/YYYY.")   
        
    return render_template("signup.html")

@app.route('/login', methods = ["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form.get("email")
        password = request.form.get("password")
        mode = "consumer"
         
        check_user = db.execute("SELECT * FROM customers WHERE email = :email AND password = :pass", {"email": str(email), "pass": str(password)}).fetchone()
        if check_user == None:
            check_user = db.execute("SELECT * FROM businesses WHERE email = :email AND password = :pass", {"email": str(email), "pass": str(password)}).fetchone()
            mode = "business"
            name = check_user["business_name"]
        else:
            name = check_user["fullname"]
                
        if check_user == None:
            return render_template("login.html", error_message = "That didn't work. Check the spelling of your username and password, and whether you have created an account at all.")
        else:
            session['logged_in'] = True
            session['fullname'] = name
            session['address'] = check_user["coordinates"]
            
            if mode == "consumer":
                return redirect(url_for("tracker", restaurant_name = "The Black Sheep Cafe"))
            else:
                return redirect(url_for("stocktake", indicator="low"))
        
    return render_template("login.html", logged_in = False, error_message = "")

@app.route('/tracker/<string:restaurant_name>')
def tracker(restaurant_name):
    try:
        if session["logged_in"]:
            distance_array = []
            all_restaurants_names = list(db.execute("SELECT business_name FROM businesses").fetchall())
            all_restaurants_addresses = list(db.execute("SELECT main_address FROM businesses").fetchall())
            all_restaurants_cuisines = list(db.execute("SELECT cuisine_type FROM businesses").fetchall())
            restaurant_cuisine = list(db.execute("SELECT cuisine_type FROM businesses WHERE business_name = :business_name", {"business_name": restaurant_name}).fetchone())[0]
            restaurant_waste = list(db.execute("SELECT waste_level FROM businesses WHERE business_name = :business_name", {"business_name": restaurant_name}).fetchone())[0]
            restaurant_address = list(db.execute("SELECT main_address FROM businesses WHERE business_name = :business_name", {"business_name": restaurant_name}).fetchone())[0]
            restaurant_coords = list(db.execute("SELECT coordinates FROM businesses WHERE business_name = :restaurant_name", {"restaurant_name": restaurant_name}).fetchone())[0]
            restaurant_menu = str(list(db.execute("SELECT menu FROM businesses WHERE business_name = :restaurant_name", {"restaurant_name": restaurant_name}).fetchone())[0])
            foodlist = restaurant_menu.replace("(", "").replace(")", "").replace("'", "")
            foodlist = foodlist[0:len(foodlist)]
            foodlist = json.loads(foodlist)
            origin_coordinates_arr = session["address"].replace("(", "").replace(")", "").split(",")
            origin_coordinates = (float(origin_coordinates_arr[1]), float(origin_coordinates_arr[0]))
            reverse_origin_coordinates = str(origin_coordinates_arr[1]) + "," + str(origin_coordinates_arr[0])
            reverse_destination_arr = restaurant_coords.replace("(", "").replace(")", "").split(",")
            reverse_destination_tuple = (float(reverse_destination_arr[1]), float(reverse_destination_arr[0]))
            reverse_destination_coordinates = str(reverse_destination_arr[1]) + "," + str(reverse_destination_arr[0])
            distance_array.append(origin_coordinates)
            distance_array.append(reverse_destination_tuple)
            distance_matrix = openrouteservice.distance_matrix.distance_matrix(client, distance_array, profile = 'driving-car', sources = [0], destinations = [1])
            restaurantlist = [[]]
            for j in range(0, len(all_restaurants_names)):
                restaurantlist[j].append(all_restaurants_names[j][0])
                restaurantlist[j].append(all_restaurants_addresses[j][0])
                restaurantlist[j].append(all_restaurants_cuisines[j][0])
                restaurantlist.append([])
            url = str('https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf6248065eabf9d1e1454bbef78fe96f3016ec&start=' + reverse_origin_coordinates + '&end=' + reverse_destination_coordinates).replace(" ", "")
            with urllib.request.urlopen(url) as url2:
                data = json.loads(url2.read().decode())
            if request.method == 'POST':
                food_item = request.form.get("fooditem")
                foodlist[food_item][1] = int(foodlist[food_item][1]) - 1
                foodlistjson = json.dumps(foodlist)
                db.execute("UPDATE menu SET menu = :foodlistjson WHERE restaurant_name = :restaurant_name", {"foodlistjson": foodlistjson, "restaurant_name": restaurant_name})
                db.execute("INSERT INTO orders (business_name, fooditem, customer_name, datetime, customer_address) VALUES (:business_name, :fooditem, :customer_name, :datetime, :customer_address)", {"business_name": restaurant_name, "orders": food_item, "customer_name": session["fullname"], "customer_address": customer_address})
                db.commit()
                return render_template("tracker.html", distance = "Distance between you and the restaurant: " + str(math.ceil(distance_matrix['durations'][0][0] / 60)) + " minutes", data = data, restaurantlist = restaurantlist, restaurant_name = restaurant_name, waste_level = restaurant_waste, cuisine = restaurant_cuisine, address = restaurant_address, logged_in = True, foodlist = foodlist)
            return render_template("tracker.html", distance = "Distance between you and the restaurant: " + str(math.ceil(distance_matrix['durations'][0][0] / 60)) + " minutes", data = data, restaurantlist = restaurantlist, restaurant_name = restaurant_name, waste_level = restaurant_waste, cuisine = restaurant_cuisine, address = restaurant_address, logged_in = True, foodlist = foodlist)

    except KeyError:
        return render_template("login.html", error_message = "You need to login to use the tracker.")        
@app.route('/business_signup', methods = ["GET", "POST"])
def business_signup():
    if request.method == 'POST':
        business_name = request.form.get("business_name")
        address = request.form.get("address")
        phone = request.form.get("phone")
        email = request.form.get("email")
        password = request.form.get("password")
        cuisine_type = request.form.get("cuisine_type")
        if str(business_name) == '' or str(address) == '' or str(phone) == '' or str(email) == '' or str(password) == '' or str(cuisine_type) == '':
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
                    session["fullname"] = business_name
                    db.execute("INSERT INTO businesses (business_name, coordinates, phone, email, password, cuisine_type, main_address, menu, orders, waste_level) VALUES (:business_name, :address, :phone, :email, :password, :cuisine_type, :main_address, :menu, :orders, :waste_level)", {"business_name": business_name, "address": "", "phone": 0, "email": str(email), "password": "", "cuisine_type": cuisine_type, "main_address": address, "menu": json.dumps({}), "orders": json.dumps({}), "waste_level": "low" })
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
                    db.execute("UPDATE businesses SET coordinates = :address WHERE email = :email", {"address": str(lat_long), "email": email})
                    session["address"] = str(lat_long)
                    
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
            return redirect(url_for("stocktake", indicator="low"))
                
    return render_template("business_signup.html")

@app.route('/stocktake/<string:indicator>', methods = ['GET', 'POST'])
def stocktake(indicator):
    selectionlist = ["Low", "Moderately Low", "Moderate", "Moderately High", "High"]
    indicatorlist = ["low", "moderately-low", "moderate", "moderately-high", "high"]
    menu = str(list(db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}))[0])
    if menu == '':
        foodlist = {}
    else:
        foodlist = menu.replace("(", "").replace(")", "").replace("'", "")
        foodlist = foodlist[0:len(foodlist) - 1]
        foodlist = json.loads(foodlist)
    
    db.execute("UPDATE businesses SET waste_level = :waste_level WHERE business_name = :name", {"waste_level": indicator, "name": session["fullname"]}) 
    db.commit()
    return render_template("stocktake.html", indicator = indicator, selectionlist = selectionlist, indicatorlist = indicatorlist, foodlist = foodlist)

@app.route('/stocktake_add_item/<string:indicator>', methods = ['GET', 'POST'])
def stocktake_add_item(indicator):
    previous_menu = str(list(db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}))[0])
    if previous_menu == '':
        foodlist = {}
    else:
        foodlist = previous_menu.replace("(", "").replace(")", "").replace("'", "")
        foodlist = foodlist[0:len(foodlist) - 1]
        foodlist = json.loads(foodlist)
    if request.method == 'POST':
        itemname = request.form.get("itemname")
        discounted_price = request.form.get("discounted_price")
        quantity = request.form.get("quantity")
        foods = str(list(db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}))[0])
        if str(foods) == '':
            foodlist = {}
            foodlist[itemname] = [str(discounted_price), quantity]
            foodlistjson = str(json.dumps(foodlist))
            db.execute("UPDATE businesses SET menu = :foodlistjson WHERE business_name = :name", {"name": session["fullname"], "foodlistjson": foodlistjson})
            db.commit()
            return redirect(url_for("stocktake", indicator = indicator)) 
        else:
            foods = foods.replace("(", "").replace(")", "").replace("'", "")
            foods = foods[0:len(foods) - 1]
            foodlist = json.loads(foods)
            foodlist[itemname] = [str(discounted_price), quantity]
            foodlistjson = str(json.dumps(foodlist))
            db.execute("UPDATE businesses SET menu = :foodlistjson WHERE business_name = :name", {"name": session["fullname"], "foodlistjson": foodlistjson})
            db.commit()
            return redirect(url_for("stocktake", indicator = indicator))
        
    return render_template("stocktake.html", indicator = indicator, button_clicked = True, foodlist = foodlist)

@app.route('/orders')
def orders():
    return render_template("orders.html")

@app.route('/business_mode')
def business_mode():
    return render_template("business_mode.html")

@app.route('/search')
def search():
    return "This is supposed to be a search."
