# RPi IoT Web Controller

A Raspberry Pi-based IoT web application that provides authenticated remote control of GPIO-connected hardware (LEDs/garage door mechanism) through a browser interface. Built as a collaborative IoT course project using Python, Flask, and the gpiozero library.

The system runs a local web server on the Raspberry Pi, allowing authorized users to toggle hardware states remotely while enforcing role-based access, session security, and account lockout protection.

---

## My Contributions

This was a team project. I co-developed the backend application logic across multiple areas:

**Authentication & Session Management**
- Co-developed the login flow in `app.py` including session-based login state tracking
- Contributed to the failed attempt counter logic and account lockout trigger after 3 failed attempts
- Helped implement session key management using `secrets.token_urlsafe()`

**User Management**
- Co-developed the `adduser` route and form — hashes new passwords with SHA-256 + salt before writing to CSV
- Contributed to `read_from_csv_file()` and `write_to_csv_file()` functions for persistent user storage
- Helped build the admin-only `viewAccounts` route rendering all stored users

**Account Unlock System**
- Co-developed the `unlock_message()` function — generates a secure one-time unlock code and sends it via Gmail SMTP
- Contributed to the `/unlock` route — validates the code, resets lockout state, and restores session access

**Frontend / Templates**
- Co-developed HTML templates including `adduser.html`, `admindashboard.html`, and supporting pages
- Contributed to the shared `style.css` — purple-themed UI with hover states, transitions, and responsive login form

---

## How It Works

```
[Browser] → [Flask Web Server on RPi] → [GPIO Pins] → [LEDs / Hardware]
```

1. User logs in via browser — credentials checked against hashed CSV records
2. On success, session is established and user reaches the hardware control page
3. Clicking on/off buttons sends URL-based commands (`/<pin>/<action>`) to Flask
4. Flask updates the GPIO pin state via gpiozero and re-renders the page
5. Admin user (`roger`) gets access to a separate dashboard for user management

---

## Features

**Authentication**
- SHA-256 password hashing with salt via `passcred.py`
- Session-based login state with Flask's signed session cookies
- Account lockout after 3 failed login attempts
- One-time email unlock code sent via Gmail SMTP
- Secure unlock flow at `/unlock`

**Role-Based Access**
- Standard users: hardware control only
- Admin (`roger`): hardware control + user management dashboard
- All protected routes check session state and redirect to login if unauthorized

**User Management (Admin only)**
- Add new users with hashed passwords via `/adduser`
- View all accounts via `/accounts`
- Users persisted to `users_data.csv`

**Hardware Control**
- Toggle Red LED (GPIO 23) and Green LED (GPIO 24) via web UI
- Live pin state reflected on page after each action
- GPIO cleanup on app exit (KeyboardInterrupt / finally block)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3 |
| Web Framework | Flask |
| Hardware Interface | gpiozero |
| GPIO Platform | Raspberry Pi |
| Templating | Jinja2 (Flask) |
| Auth | SHA-256 + salt (hashlib) + Flask sessions |
| Email | smtplib (Gmail SMTP SSL) |
| Storage | CSV (csv.DictReader / DictWriter) |
| Frontend | HTML + CSS (vanilla) |

---

## Project Structure

```
project/
├── app.py                  — main Flask application
├── adduserfunction.py      — standalone add user utility
├── passcred.py             — password salt (DO NOT COMMIT — see security note)
├── emailcred.py            — email credentials (DO NOT COMMIT — see security note)
├── users_data.csv          — user storage (auto-generated on first add)
├── templates/
│   ├── login.html
│   ├── main.html
│   ├── admindashboard.html
│   ├── adduser.html
│   ├── accounts.html
│   └── unlock.html
└── static/
    └── style.css
```

---

## Setup & Running

### Prerequisites
- Raspberry Pi with Raspbian OS
- Python 3
- Flask and gpiozero installed

```bash
pip install flask gpiozero
```

### Configuration

Create `passcred.py` with your salt and hashed password (do not commit):
```python
import hashlib, secrets
salt = secrets.token_urlsafe(16)
hashed_password = hashlib.sha256((salt + "yourpassword").encode()).hexdigest()
```

Create `emailcred.py` with your Gmail credentials (do not commit):
```python
FROM = 'youremail@gmail.com'
TO   = 'youremail@gmail.com'
PASS = 'your-app-password'
```

> Gmail requires an App Password (not your account password). Enable 2FA on your Google account and generate one under Security → App Passwords.

### Run

```bash
sudo python3 app.py
```

> `sudo` required for GPIO access on port 80. Navigate to `http://<your-pi-ip>` in a browser on the same network.

---

## Security Notes

- `emailcred.py` and `passcred.py` are excluded from this repo via `.gitignore` — never commit real credentials
- Passwords are never stored in plaintext — SHA-256 + salt hashing applied at registration and login
- Flask `SECRET_KEY` is randomly generated per session via `secrets.token_urlsafe(16)`
- Account lockout and email-based unlock add a basic brute-force protection layer
