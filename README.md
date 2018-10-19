# Vent

## Introduction

>Vent is an application that allows users to discover events near them. It handles the discovery of events, as well as coordination between the attendees and organisers. All messages and questions occur in real time by utilizing web push technology and server sent events.

## Installation

> You will need:
*  Python 3.X (tested on 3.6.5)
* Gunicorn (only available on linux)
* MySQL
* Redis
* OpenSSL

1. Clone the application with `git clone https://github.com/j-chad/event-app.git`
2. Create an instance folder in the root
     1.  Create a config.py variable inside
     2. config.py must have the following variables defined:
         * SECRET_KEY: this is just a random string (should be generated with a CSPRNG). You can use `os.urandom`.
         * HASHID_SALT: another random string. use a CSPRNG.
         * MAIL_PASSWORD: the password to your email server.
         * RECAPTCHA_PRIVATE_KEY: you can obtain this from the [google recaptcha console](https://www.google.com/recaptcha/admin)
         * SQLALCHEMY_DATABASE_URI: the sqlaclhemy uri pointing to your mysql database.
         * WEB_PUSH_PRIVATE_KEY, WEB_PUSH PUBLIC_KEY: These two variables can be optained from [this site](https://web-push-codelab.glitch.me/)
3. Create a virtual environment and install the packages from requirements.txt
4. Create a certificate so that the application can use https. `openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365`
5. change variables in configs.py such as:
    * MAIL\_USERNAME, MAIL\_SERVER, MAIL_...
    * RECAPTCHA_PUBLIC_KEY
    * MAPBOX_ACCESS_TOKEN
6. Add `127.0.0.1	http://vent.local	vent.local` to your hosts file
7. `flask build_database`
8. `gunicorn autoapp:app --worker-class gevent --certfile key.pem --keyfile cert.pem --reload --env="FLASK_ENV=production" --bind 0.0.0.0:8000`
9. Seperately, run `flask rq worker`
10. Browse to https://vent.local:8000/ (you may have to add an exception for the certificate)