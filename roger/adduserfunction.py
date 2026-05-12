from gpiozero import LED, Buzzer
from flask import Flask, render_template, request, redirect, flash, session
from hashlib import sha256
from time import sleep
from datetime import datetime
import smtplib
import secrets
import hashlib
import passcred
import csv
from datetime import datetime
from pathlib import Path

csv_file_path = Path("users_data.csv")
user_record = {
    "Name": None,
    "Password": None,
}


app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)

def write_to_csv_file(add_this_record):
    first_write = not csv_file_path.is_file()

    with open(csv_file_path, "a") as file:
        field_names = user_record.keys()
        writer = csv.DictWriter(file, field_names)
        if first_write:
            writer.writeheader()
        writer.writerow(add_this_record)


@app.route("/")
def home():
    return render_template('adduser.html')

@app.route('/adduser', methods=['POST', 'GET'])
def adduser():
    user_record["Name"] = request.form['new_username']
    password = request.form['new_password']
    
    new_hash = hashlib.sha256((passcred.salt + password).encode('utf-8')).hexdigest()
    user_record['Password'] = new_hash
    write_to_csv_file(user_record)

    
    


    return render_template('adduser.html')

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=80, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")

