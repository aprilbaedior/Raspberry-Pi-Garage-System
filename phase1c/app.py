'''
Make sure to organize the files as follows:
phase1c (folder)
|__ app.py
|__ templates (folder)
|	|__ main.html
|	|__ login.html
|__ static (folder)
	|__ style.css

** The current username is roger, the password is roger123
'''
#import RPi.GPIO as GPIO
import hashlib
import smtplib
from gpiozero import LED
from signal import pause
from time import sleep
from flask import Flask, render_template, request, flash, redirect, session
import passcred
import emailcred
import secrets

# importing the needed libraries for csv files
import csv
from datetime import datetime
from pathlib import Path

csv_file_path = Path("users_data.csv")
user_record = {
    "Username": None,
    "Password": None,
    "Email": None
}

red_LED = None
green_LED = None

try:
    # This creates an instance of a Flask application
    app = Flask(__name__)
    app.config['SECRET_KEY'] = secrets.token_urlsafe(16)    # read the NOTE below
    '''
    Note:
    1) app.config: This is a dictionary-like object used to store configuration settings for your Flask application.

    2) SECRET_KEY: This is a special configuration key in Flask, often used for securing sessions, cookies, 
    or other sensitive operations like CSRF (Cross-Site Request Forgery) protection. 
    The SECRET_KEY ensures that any data signed by your app (e.g., session cookies) cannot be tampered with by a client.

    3) secrets.token_urlsafe(16): This generates a secure, random string of 16 bytes encoded in a URL-safe format, 
    which is perfect for use as a cryptographic key. It ensures a high level of randomness and security.
    '''

    red_LED_GPIO = 23
    green_LED_GPIO = 24

    red_LED = LED(red_LED_GPIO) 
    green_LED = LED(green_LED_GPIO)

    # Create a dictionary called pins to store the pin number, name, and pin state:
    pins = {
       23 : {'var_name' : red_LED, 'state' : False, 'description' : 'The Red LED'},
       24 : {'var_name' : green_LED, 'state' : False, 'description' : 'The Green LED'}
       }

    # Assigne each pin as an LED and turn it off
    for pin in pins:
        led_name = pins[pin]['var_name']
        led_name.off()
    
    '''
    Note:
    1)session: In Flask, session is a special object used to store information about a user's session, 
    such as login status or preferences. 
    Data stored in session is unique to each user and typically backed by cookies or server storage. 
    Flask uses the SECRET_KEY (as we discussed earlier) to securely sign this data.

    2).get('logged_in'): The .get() method is used to retrieve the value associated with the key 'logged_in' from the session object. 
    If the key doesn't exist, it will return None by default (instead of raising an error).
    '''
    
    def read_from_csv_file():
        #create a list to store the user data
        accounts = []
        if not csv_file_path.is_file():
            print("File does not exist ...")
            return accounts
    # use: "r" for read, "w" for write, "a" for append
        with open(csv_file_path, "r") as file: 
            reader = csv.DictReader(file)
            for row in reader:
                #add the rows to the list
                accounts.append(row)
        return accounts
    

    def write_to_csv_file(add_this_record):
        first_write = not csv_file_path.is_file()

        with open(csv_file_path, "a") as file:
            field_names = ["Username", "Password", "Email"]
            writer = csv.DictWriter(file, field_names)
            if first_write:
                writer.writeheader()
            writer.writerow(add_this_record)

    @app.route("/")
    def home():
        # This checks if the retrieved session value 'logged_in' is True
        if not session.get('logged_in'):
            # if the 'logged_in' is not True, the user will be directed to the login.html page
            return render_template('login.html')
        else:
            return redirect('/main')
            
        
    @app.route('/login', methods=['POST'])
    def do_admin_login():
        #request username and password from html and store in variables 
        username = request.form['username']
        password = request.form['password']

        #check if user acccount already locked out as soon as they enter their creditentials
        if session.get('locked', False):
            flash("Account is locked. Instructions to unlock have been sent to the admin email.")
            return home()

        else:
            #read user data from csv file and store in a variable
            accounts = read_from_csv_file()

            #create a loop through the users
            for user in accounts:
                if username == user['Username']:
                    #hash the user input with salt from passcred and store in variable
                    hashing = hashlib.sha256((passcred.salt + password).encode('utf-8')).hexdigest()

                    #compare username with csv file usernames and the hashing result with hashed pw in csv
                    if hashing == user['Password']:
                        #update the session when login is successful
                        session['logged_in'] = True
                        session['username'] = username
                        #clear failed attempts once login is successful
                        session['failed_attempts'] = 0

                        if username == 'roger':
                            flash('Welcome Uncle Roger!')
                            return render_template('admindashboard.html')
                        else:
                            flash('Welcome!')
                            return redirect("/main")
                
            session['failed_attempts'] = session.get('failed_attempts', 0) + 1

            #lock account after 3 tries
            if session['failed_attempts'] >= 3:
                session['locked'] = True
                flash("You have been locked out after 3 failed attempts.")
                unlock_message()
                return render_template('unlock.html')
            else:
                flash('Wrong username or password! Try again.')  
                return home()
        
    #admindashboard only accessible by Uncle Roger
    @app.route('/admindashboard', methods=['GET', 'POST'])
    def admin_dashboard():
        #check that user is logged in
        if not session.get('logged_in'):
            flash("You must be logged in to access the admin dashboard.")
            return home()

        #check that user is 'roger'
        if session.get('username') != 'roger':
            flash("Access denied. Only Uncle Roger can access this page.")
            return home()
        #render the admin dashboard page if user is 'roger'
        
        return render_template('admindashboard.html')
        

    #add a user page and functionality
    @app.route('/adduser', methods=['GET', 'POST'])
    def adduser():
        if request.method == 'POST':
            username = request.form['new_username']
            password = request.form['new_password']
            email = request.form['new_email']
            
            new_hash = hashlib.sha256((passcred.salt + password).encode('utf-8')).hexdigest()
            new_user = {
             "Username": username,
             "Password": new_hash,
             "Email": email
            }
            write_to_csv_file(new_user)
            return render_template('adduser.html')
        return render_template('adduser.html')
        
    #view accounts only for admin
    @app.route('/accounts', methods = ['GET'])
    def viewAccounts():
        #check that user is 'roger' (admin)
        if session.get('username') != 'roger':
            flash("Access denied. Only Uncle Roger can access this page.")
            return home()
        
        users = [] #stores the csv in array
        if csv_file_path.is_file(): #if there is a file 
            with open(csv_file_path, newline='') as file: #opens file and reads one line at a time
                reader = csv.DictReader(file)
                for row in reader: 
                    users.append(row) #goes through each row
        return render_template("accounts.html", users=users)

    def unlock_message():
        #generate unlock code
        unlock_code = secrets.token_urlsafe(4)
        # save code to session
        session['unlock_code'] = unlock_code  

        message = (
            "\nHello,\n"
            "Your account has been locked after 3 failed login attempts.\n\n"
            f"Unlock Code: {unlock_code}\n\n"
            "Please go to the unlock page to enter your code and regain access.")

        #send the message via email
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(emailcred.FROM, emailcred.PASS)
        server.sendmail(emailcred.FROM, emailcred.TO, message)
        server.quit()
        print("Unlock email sent.")
        
    @app.route('/unlock', methods=['GET','POST'])
    def unlock():
        if request.method == 'POST':
            #create a variable to store code and get from form
            code = request.form['code']
        
            #check if the code matches
            if code == session.get('unlock_code'):
                #unlock the account by setting locked to False
                session['locked'] = False
                #reset failed login attempts
                session['failed_attempts'] = 0
                flash('Account unlocked. You can now log in.')
                return redirect('/')
            else:
                #reload page if invalid
                flash('Incorrect unlock code.')
                return render_template('unlock.html')
        return render_template('unlock.html')
                
            

    @app.route("/logout")
    def logout():
        # update the session value 'logged_in' to False
        session['logged_in'] = False
        return home()


    @app.route("/main")
    def main():
        # check if the user logged_in to the system
        if not session.get('logged_in'):
            return render_template('login.html')
        else:
            # For each pin, read the pin state and store it in the pins dictionary:
            for pin in pins:
                LED_name = pins[pin]['var_name']
                pins[pin]['state'] = LED_name.is_lit
                print("in main pin {pin} is: ", pins[pin]['state'])
              
            # Put the pin dictionary into the template data dictionary:
            templateData = {
              'pins' : pins
              }
            
            # Pass the template data into the template main.html and return it to the user
            return render_template('main.html', **templateData)
            

    # The function below is executed when someone requests a URL with the pin number and action in it:
    @app.route("/<changePin>/<action>")
    def action(changePin, action):
        if not session.get('logged_in'):
            return render_template('login.html')
        else:
            # Convert the pin from the URL into an integer:
            changePin = int(changePin)
            # Get the LED name for the pin being changed:
            LED_name = pins[changePin]['var_name']
            # If the action part of the URL is "on," execute the code indented below:
            if action == "on":
                # Set the pin high:
                LED_name.on()
                #print("the action is on for: ", LED_name)
                # Save the status message to be passed into the template:
                message = "Turned " + str(changePin) + " on."
            if action == "off":
                LED_name.off()
                print("the action is off for: ", LED_name)
                message = "Turned " + str(changePin) + " off."

            # For each pin, read the pin state and store it in the pins dictionary:
            for pin in pins:
                LED_name = pins[pin]['var_name']
                pins[pin]['state'] = LED_name.is_lit
                #print(f'pin number {pin} is', pins[pin]['state'])

            # Along with the pin dictionary, put the message into the template data dictionary:
            templateData = {
              'pins' : pins
            }
            return render_template('main.html', **templateData)
            

    # run Flask application
    if __name__ == "__main__":
        print("Enter Ctrl+C to exit.")
        app.run(host='0.0.0.0', port=80, debug=False)
        
        
except KeyboardInterrupt:
    # Handle Ctrl+C gracefully
    print("\nExiting the program...")
    

finally:
    # Cleanup resources
    print("Closing the Flask app.")
    print("Cleaning up GPIO pins...")
    red_LED.off()           # Ensure the red LED is turned off
    red_LED.close()         # Release the GPIO pin for the red LED
    green_LED.off()         # Ensure the green LED is turned off
    green_LED.close()       # Release the GPIO pin for the green LED
