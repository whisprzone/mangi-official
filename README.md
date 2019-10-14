
# mangi: food waste tracker and delivery
CEP Final Project by Koo Yu Tang and Surya Nayar
September-October 2019

INTRODUCTION:
mangi reduces food waste by allowing you to track nearby restaurants and cafes that have good
but leftover food, which would otherwise be thrown away at the end of the day. "mangi" means
"eat" in Italian, which emphasises our mission to reduce food waste, contributing to social good.
Consumers can go to the restaurant to get the food or order food delivery right
to their doorstep.<br><br>
Businesses can sign up for a business account and update their leftover food
menu to be cleared by selling it at a discounted price to consumers.

VIDEO:
Watch the introduction video first  
link: https://www.youtube.com/watch?v=y92ZTroJ2aE  

------------------

INFORMATION ABOUT EACH FILE:  
* __pycache__ folder: ignore this folder  
* application.py: the main Python code that runs the website  
* flask_session folder: contains information about the flask session when you run the website  
* README.md: introductory file that you are reading right now  
* requirements.txt: list of Python libraries that you must download for the code to work  
* static folder: contains the CSS file for the styling of the website and the image files  
* templates folder: contains the HTML files for displaying information on the website  

----------------------

REQUIREMENTS TO RUN WEBSITE:  
* Python 3  
* Flask  
* PostgreSQL  
For the list of Python libraries, refer to requirements.txt  

If you are using Python 3.7 on MacOS, run this command in the terminal to update
Python certificates in order for geopy to run properly:
/Applications/Python\ 3.7/Install\ Certificates.command

HOW TO RUN WEBSITE:
1. Open up your terminal window  
2. Navigate into the CEP Final Project folder  
3. Run "pip3 install -r requirements.txt" in your terminal window to make sure that all of the necessary Python packages are installed  
4. Set the environment variable FLASK_APP to be application.py. On a Mac or on Linux, the command to do this is "export FLASK_APP=application.py". On Windows, the command is instead "set FLASK_APP=application.py" in Command Prompt (preferable) and set $FLASK_APP=application.py in PowerShell  
5. Type "flask run" in the terminal window  
6. Go to the URL provided by flask (usually http://127.0.0.1:5000/)  
7. Tada! The website is now running!  

--------------------

FEATURES:
Homepage (before sign in):  
- Beautiful front landing page  
- "Start Now" button leads to sign up page  
- Custom designed mangi logo  
- Introduction section when you scroll down
- Search button and panel (although the search function does not work)
- Consumer signup page
- Business signup page
- Login page for consumers and businesses
- Checks to ensure that all fields in the signup pages and login page are filled
  in correctly

NOTE:
Address must be a real address and it should only include road number and name,
do not include the shop/ house unit or postal code (so that the map api will work)
Credit card number must be 16 digits long and start with either 3, 4, 5 or 6 so
that it is a valid credit card number. CVVs are three digits long and expiration dates
are in the form mm/yyyy.

Consumer Mode:
- Tracker page with a restaurant list to locate nearby restaurants (left panel)
- Interactive map to show the travelling route to the selected restaurant (for food self-collection)
- Estimated travelling distance (mins) to the selected restaurant
- Restaurant info including food waste level, cuisine type, address (right panel)
- Leftover food section displays food items, quantity and discounted price
- Click on the add icon to order the food item. The bill is charged to the consumer's
  credit card number (in theory)
- Delivery page displaying the food orders
- Food orders can be cancelled by clicking on the minus icons
- Settings page displaying account info
- Delete account
- Logout button

Business Mode:
- Stocktake page for restaurants to update their general food waste level and menu
- Update the food items' names, quantities and prices that have changed (don't need
  to fill up all the fields in the form) and click the update button
- Add new food items to the menu by clicking the add icon
- Orders page displaying the incoming food orders from consumers
- Tick on food orders when they have been delivered to the consumer
- Settings page displaying account info
- Delete account
- Logout button

INCOMPLETE/ FUTURE IMPROVEMENTS:
- Search function to search nearby restaurants (although its not really necessary as
  most people would want to see restaurants near them to order food)
- Edit user information in the Settings page (not enough time to implement)
- For the consumer account, add the food order to a food cart for the person
  to confirm purchase and billing method first, instead of adding it directly to
  the delivery page as a food order

------------------

SUMMARY:
Overall very proud of this project as we spent more than 200 hours in total thinking
of the idea, designing the frontend user interface, learning and implementing the map api,
and integrating everything all together into one functional website through all the
challenges and miscommunications.
