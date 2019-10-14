
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_session import Session
from geopy.geocoders import Nominatim
import random, os, json, omdb, re, socket, openrouteservice, geocoder, math, urllib
from datetime import datetime

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
    # use try and except to check whether the user exists
    try:
        return render_template("home.html", logged_in = session["logged_in"])
    except KeyError:
        return render_template("home.html", logged_in = False)

@app.route('/logout')
def logout():
    # logs out user, sets all session variables to none
    session["logged_in"] = None
    session["fullname"] = None
    session['address'] = None
    session['main_address'] = None
    session['indicator'] = None
    session['mode'] = None
    return redirect(url_for("index"))

@app.route('/delivery')
def delivery():
    db_orders = list(db.execute("SELECT * FROM orders WHERE customer_name = :name", {"name": session["fullname"]}).fetchall()) # data fed in from table in database (orders)
    if len(db_orders) != 0:
        for i in range(0, len(db_orders)):
            row_dict = dict(db_orders[i])
            orders[i].append(row_dict["foodname"])
            orders[i].append(row_dict["business_name"])
            orders[i].append(row_dict["datetime"])
            if i < (len(db_orders) - 1): # to ensure that there isn't an empty array at the end for no reason
                orders.append([])
        return render_template("delivery.html", orders = orders)


    else:
        return render_template("delivery.html", orders = [])


    

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

        # first check for whether any fields are blank
        if str(fullname) == '' or str(address) == '' or str(phone) == '' or str(email) == '' or str(password) == '' or str(creditcard) == '' or str(cvv) == '' or str(expiration) == '':
            return render_template("signup.html", error_message = "Please ensure all fields are filled up.")

        else:

            email = str(email)
            arr = []
            # use regex (re) to find number of @ in email (has to be only one to allow user to proceed)
            for match in re.finditer('@', email):
                arr.append(match)

            if len(arr) == 1:
                check_email = list(db.execute("SELECT email FROM customers WHERE email = :email", {"email": email}))
                if check_email != []:
                    email = ''
                    return render_template("signup.html", error_message = "There is an already an account associated with this email account.")
                else:
                    db.execute("INSERT INTO customers (email, password, coordinates, phone, creditcard, fullname, cvv, expiration, main_address, orders) VALUES (:email, :password, :address, :phone, :creditcard, :fullname, :cvv, :expiration, :main_address, :orders)", {"email": str(email), "password": "", "address": "", "phone": 0, "creditcard": 0, "fullname": fullname, "cvv": 0, "expiration": "", "main_address": address}) # temporarily dumps all values into database without commit
            else:
                email = []
                return render_template("signup.html", error_message = "Please enter a valid email address.")
            # minimum password length is 6 without spaces
            if email != '':
                if len(str(password)) >= 6 and ' ' not in str(password):
                    db.execute("UPDATE customers SET password = :password WHERE email = :email", {"password": str(password), "email": email}) 

                else:
                    return render_template("signup.html", error_message = "Your password needs to be at least 6 characters long and should not contain spaces.")

                # SG credit cards are 16 digits long and start with 3, 4, 5, 6, 
                if len(str(creditcard)) == 16 and (str(creditcard)[0] == "3" or str(creditcard)[0] == "4" or str(creditcard)[0] == "5" or str(creditcard)[0] == "6"):
                    try:
                        db.execute("UPDATE customers SET creditcard = :creditcard WHERE email = :email", {"creditcard": int(str(creditcard)), "email": email})

                    except ValueError:
                        return render_template("signup.html", error_message = "Please enter a valid credit card number.") 

                else:
                    return render_template("signup.html", error_message = "Please enter a valid credit card number.")

                # cvv is a 3-digit int
                if len(cvv) == 3:
                    try:
                        db.execute("UPDATE customers SET cvv = :cvv WHERE email = :email", {"cvv": int(str(cvv)), "email": email})

                    except ValueError:
                        return render_template("signup.html", error_message = "Please enter a valid CVV.")

                else:
                    return render_template("signup.html", error_message = "Please enter a valid CVV.")

                try: # because the geolocator sometimes returns socket timed out errors randomly, two tries are required 
                    location = geolocator.geocode(str(address), timeout = None)
                    lat_long = (location.latitude, location.longitude)

                except: # should work on second try (in our experience)
                    location = geolocator.geocode(str(address))
                    lat_long = (location.latitude, location.longitude)

                # warn people not to use postal codes - trips up the geolocator
                if location != None and "Singapore" in str(location):
                    db.execute("UPDATE customers SET coordinates = :address WHERE email = :email", {"address": str(lat_long), "email": email})
                    session["address"] = str(lat_long)
                    session["main_address"] = str(location) # separation of coordinates and location so the user has an easier time (and so do we)

                else:
                    return render_template("signup.html", error_message = "Please enter a valid address. Valid addresses include street/road name and a number, like 9 Bishan Place or 1 Raffles Institution Lane. Addresses must be located in Singapore. Do not include postal codes.")

                # phone numbers 8 digits long
                if len(str(phone)) == 8:
                    try:
                        db.execute("UPDATE customers SET phone = :phone WHERE email = :email", {"phone": int(str(phone)), "email": email})
                    except ValueError:
                        return render_template("signup.html", error_message = "Please enter a valid phone number. Singapore phone numbers contain only 8 digits.")

                else:
                    return render_template("signup.html", error_message = "Please enter a valid phone number. Singapore phone numbers contain only 8 digits.")

                # expiration of format mm/yyyy 
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
                                session["main_address"] = address
                                session["mode"] = "consumer"
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
        mode = "consumer" # by default the person who's logging in is more likely to be a consumer
         
        check_user = db.execute("SELECT * FROM customers WHERE email = :email AND password = :pass", {"email": str(email), "pass": str(password)}).fetchone()
        if check_user == None:
            check_user = db.execute("SELECT * FROM businesses WHERE email = :email AND password = :pass", {"email": str(email), "pass": str(password)}).fetchone() # check both tables
            mode = "business"
            if check_user != None:
                name = check_user["business_name"]
        else:
            name = check_user["fullname"]
                
        if check_user == None:
            return render_template("login.html", error_message = "That didn't work. Check the spelling of your username and password, and whether you have created an account at all.")
        else:
            session['logged_in'] = True # set all session variables to True/other variants
            session['fullname'] = name
            session['address'] = check_user["coordinates"]
            session['main_address'] = check_user["main_address"]
            if mode == "consumer":
                session["mode"] = "consumer"
                return redirect(url_for("tracker")) # consumer tracker page
            else:
                session["mode"] = "business"
                session["indicator"] = check_user["waste_level"]
                return redirect(url_for("stocktake", indicator=session["indicator"])) # business stocktake page

    return render_template("login.html", error_message = "")

@app.route('/settings')
def settings():
    # enable both consumers and businesses to delete their accounts if they want to
    if session["mode"] == "consumer":
        email = db.execute("SELECT email FROM customers WHERE fullname = :name", {"name": session["fullname"]}).fetchone()[0]
        phone_number = db.execute("SELECT phone FROM customers WHERE fullname = :name", {"name": session["fullname"]}).fetchone()[0]
    if session["mode"] == "business":
        email = db.execute("SELECT email FROM businesses WHERE business_name = :name", {"name": session["fullname"]}).fetchone()[0]
        phone_number = db.execute("SELECT phone FROM businesses WHERE business_name = :name", {"name": session["fullname"]}).fetchone()[0]
 
    
    return render_template("settings.html", name = session["fullname"], address = session["main_address"], email = email, phone_number = phone_number)

@app.route('/delete_account/<string:name>', methods = ["GET", "POST"])
def delete_account(name):
    # delete account subprocess (href from settings page)
    if request.method == 'POST':
        if session["mode"] == "consumer":
            db.execute("DELETE FROM customers WHERE fullname = :name", {"name": name})
            session["logged_in"] = False
            session['fullname'] = ''
            session['address'] = ''
            session['main_address'] = ""
        if session["mode"] == "business":
            db.execute("DELETE FROM businesses WHERE business_name = :name", {"name": name})
            session["logged_in"] = False
            session["fullname"] = ''
            session["mode"] = "consumer"
            session["indicator"] = ""
        db.commit() # make sure all deletions actually occur

    return redirect(url_for("index"))
@app.route('/tracker')
def tracker():
    return redirect(url_for("tracker_restaurant", restaurant_name="The Black Sheep Cafe")) # pick random restaurant to serve as initial restaurant

@app.route('/tracker/<string:restaurant_name>')
def tracker_restaurant(restaurant_name):
    try:
        if session["logged_in"]: # need to be logged in to access tracker

            # get all that we need from the database
            distance_array = []
            all_restaurants_names = list(db.execute("SELECT business_name FROM businesses").fetchall())
            all_restaurants_addresses = list(db.execute("SELECT main_address FROM businesses").fetchall())
            all_restaurants_cuisines = list(db.execute("SELECT cuisine_type FROM businesses").fetchall())
            restaurant_coords = list(db.execute("SELECT coordinates FROM businesses WHERE business_name = :restaurant_name", {"restaurant_name": restaurant_name}).fetchone())[0]

            # following lines get coordinates and manipulate them to fit the requirements of openrouteservice and api.openrouteservice.org
            origin_coordinates_arr = session["address"].replace("(", "").replace(")", "").split(",")
            origin_coordinates = (float(origin_coordinates_arr[1]), float(origin_coordinates_arr[0]))
            reverse_origin_coordinates = str(origin_coordinates_arr[1]) + "," + str(origin_coordinates_arr[0])
            reverse_destination_arr = restaurant_coords.replace("(", "").replace(")", "").split(",")
            reverse_destination_tuple = (float(reverse_destination_arr[1]), float(reverse_destination_arr[0]))
            reverse_destination_coordinates = str(reverse_destination_arr[1]) + "," + str(reverse_destination_arr[0])
            distance_array.append(origin_coordinates)
            distance_array.append(reverse_destination_tuple)
            distance_matrix = openrouteservice.distance_matrix.distance_matrix(client, distance_array, profile = 'driving-car', sources = [0], destinations = [1]) # use openrouteservice to calculate times between two locations
            restaurantlist = [[]] # to show in the panels
            for j in range(0, len(all_restaurants_names)):
                restaurantlist[j].append(all_restaurants_names[j][0])
                restaurantlist[j].append(all_restaurants_addresses[j][0])
                restaurantlist[j].append(all_restaurants_cuisines[j][0])
                restaurantlist.append([])
            url = str('https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf6248065eabf9d1e1454bbef78fe96f3016ec&start=' + reverse_origin_coordinates + '&end=' + reverse_destination_coordinates).replace(" ", "") # returns json response to enable map to work
            with urllib.request.urlopen(url) as url2:
                data = json.loads(url2.read().decode()) # use urllib2 to decode json response

            restaurant_info = db.execute("SELECT * FROM businesses WHERE business_name = :name", {"name": restaurant_name}).fetchone()

            menu_str = db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": restaurant_name}).fetchone()[0]
            menu = json.loads(menu_str) # menu is stored as json string, need to convert to dictionary

            return render_template("tracker.html", all_restaurants = "Distance between you and the restaurant: " + str(math.ceil(distance_matrix['durations'][0][0] / 60)) + " minutes", data = data, restaurantlist = restaurantlist, res_info=restaurant_info, menu = menu, restaurant_name = restaurant_name)

    except KeyError:
        return render_template("login.html", error_message = "You need to be logged in to use the tracker.") # handle situations where the guys access the tracker without logging in 

@app.route('/add_order/<string:restaurant>/<string:foodname>/<string:address>/<string:fullname>', methods = ['GET', 'POST'])
def add_order(restaurant, foodname, address, fullname):

    # enables adding order mechanism - close interface with business database
    current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    menu_str = db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": restaurant}).fetchone()[0]
    menu = json.loads(menu_str)

    menu[foodname] = [menu[foodname][0], menu[foodname][1] - 1] # subtracts quantity of food by 1 on placing of order

    menu_json = json.dumps(menu) # convert back to json string
    db.execute("UPDATE businesses SET menu = :menu WHERE business_name = :name", {"menu": menu_json, "name": restaurant})

    #update orders for the consumer to be shown in delivery page
    db.execute("INSERT INTO orders (business_name, foodname, customer_name, datetime, address) VALUES (:business_name, :foodname, :customer_name, :datetime, :address)", {"business_name": restaurant, "foodname": foodname, "customer_name": session["fullname"], "datetime": current_datetime, "address": session["main_address"]}) 

    db.commit()
    
    return redirect(url_for("delivery"))

@app.route('/business_signup', methods = ["GET", "POST"])
def business_signup():
    # essentially the same thing as signup but geared towards businesses with additional cuisine_type param

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
                    session["main_address"] = address
                    session["mode"] = "business"
                    db.execute("INSERT INTO businesses (business_name, coordinates, phone, email, password, cuisine_type, main_address, menu, waste_level) VALUES (:business_name, :address, :phone, :email, :password, :cuisine_type, :main_address, :menu, :waste_level)", {"business_name": business_name, "address": "", "phone": 0, "email": str(email), "password": "", "cuisine_type": cuisine_type, "main_address": address, "menu": json.dumps({}), "waste_level": "low" })
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

@app.route('/stocktake/<string:indicator>/', methods = ['GET', 'POST'])
def stocktake(indicator):
    selectionlist = ["Low", "Moderately Low", "Moderate", "Moderately High", "High"]
    indicatorlist = ["low", "moderately-low", "moderate", "moderately-high", "high"]
    # inform consumers how much waste a restaurant is generating

    menu_str = db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}).fetchone()[0]
    menu = json.loads(menu_str)

    session["indicator"] = indicator # special session variable for businesses
    db.execute("UPDATE businesses SET waste_level = :waste_level WHERE business_name = :name", {"waste_level": indicator, "name": session["fullname"]}) # update waste level accordingly 
    db.commit()
    return render_template("stocktake.html", indicator=indicator, selectionlist=selectionlist, indicatorlist=indicatorlist, menu=menu)


@app.route('/stocktake_add_item/<string:indicator>', methods = ['GET', 'POST'])
def stocktake_add_item(indicator):
    selectionlist = ["Low", "Moderately Low", "Moderate", "Moderately High", "High"]
    indicatorlist = ["low", "moderately-low", "moderate", "moderately-high", "high"]
    #for the URLs

    previous_menu = str(list(db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}))[0])
    if previous_menu == '':
        foodlist = {}
    else:
        foodlist = previous_menu.replace("(", "").replace(")", "").replace("'", "")
        foodlist = foodlist[0:len(foodlist) - 1]
        foodlist = json.loads(foodlist) # had to do this because menu was quite difficult to get into proper shape
    if request.method == 'POST':
        itemname = request.form.get("itemname")
        discounted_price = request.form.get("discounted_price")
        quantity = request.form.get("quantity")
        foods = str(list(db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}))[0])
        if str(foods) == '':
            foodlist = {}
            foodlist[itemname] = [str(discounted_price), int(quantity)]
            foodlistjson = str(json.dumps(foodlist))
            db.execute("UPDATE businesses SET menu = :foodlistjson WHERE business_name = :name", {"name": session["fullname"], "foodlistjson": foodlistjson}) # adds item to dictionary, converts to json, updates table
            db.commit()
            return redirect(url_for("stocktake", indicator = indicator)) 
        else:
            foods = foods.replace("(", "").replace(")", "").replace("'", "")
            foods = foods[0:len(foods) - 1]
            foodlist = json.loads(foods)
            foodlist[itemname] = [str(discounted_price), int(quantity)]
            foodlistjson = str(json.dumps(foodlist))
            db.execute("UPDATE businesses SET menu = :foodlistjson WHERE business_name = :name", {"name": session["fullname"], "foodlistjson": foodlistjson}) # same as above but menu is not empty
            db.commit()
            return redirect(url_for("stocktake", indicator = indicator))
        
    return render_template("stocktake.html", indicator = indicator, button_clicked = True, selectionlist =selectionlist, indicatorlist = indicatorlist, menu = foodlist)
@app.route('/stocktake_update', methods = ['GET', 'POST'])
def stocktake_update():
    menu_str = db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}).fetchone()[0]
    menu = json.loads(menu_str)

    for food, info in menu.items():
        food_name = request.form.get(food + " name")
        qty = request.form.get(food + " qty")
        price = request.form.get(food + " price")
        if food_name != "" and food_name != None:
            menu[food_name] = info
            menu.pop(food, None) # updates instead of adds
        else:
            food_name = food

        if qty != "" and qty != None:
            menu[food_name][1] = int(qty) # sets quantity (type int)
        if price != "" and price != None:
            menu[food_name][0] = price # sets price (type string)
        
    menu_json = json.dumps(menu)
    db.execute("UPDATE businesses SET menu = :menu WHERE business_name = :name", {"menu": menu_json, "name": session["fullname"]}) 
    db.commit() # update table and commit
    
    return redirect(url_for("stocktake", indicator=session["indicator"]))

@app.route('/stocktake_remove/<string:menuitem>', methods = ['GET', 'POST'])
def stocktake_remove(menuitem):
    menu_str = db.execute("SELECT menu FROM businesses WHERE business_name = :name", {"name": session["fullname"]}).fetchone()[0]
    menu = json.loads(menu_str) # same as stocktake_add but removes instead of adding (thanks to little - button)
    del menu[menuitem]
    new_menu = json.dumps(menu)
    db.execute("UPDATE businesses SET menu = :new_menu WHERE business_name = :name", {"new_menu": new_menu, "name": session["fullname"]})
    db.commit()

    return redirect(url_for("stocktake", indicator = session["indicator"]))

@app.route('/orders')
def orders():
    # BUSINESS section which shows all orders placed to that restaurant 
    db_orders = list(db.execute("SELECT * FROM orders WHERE business_name = :name", {"name": session['fullname']}).fetchall())
    if len(db_orders) != 0:
        orders = [[]]
        for i in range(0, len(db_orders)):
            row_dict = dict(db_orders[i])
            orders[i].append(row_dict["foodname"])
            orders[i].append(row_dict["customer_name"])
            orders[i].append(row_dict["address"])
            orders[i].append(row_dict["datetime"])
            if i < (len(db_orders) - 1):
                orders.append([]) # same situation as delivery page

        return render_template("orders.html", orders = orders)
    else:
        return render_template("orders.html", orders = [])


@app.route('/orders_tick_item/<string:datetime>', methods = ['GET', 'POST'])
def orders_tick_item(datetime):
    # so orders can be verified 
    datetime = datetime.replace("_", "/") # / was generating problems so replace with _ in jinja and convert accordiingly
    db.execute("DELETE FROM orders WHERE datetime = :datetime", {"datetime": str(datetime)})
    db.commit()
    return redirect(url_for("orders"))

@app.route('/search')
def search():
    # no search yet 
    return "Search is not enabled in the beta."
