Installation
******************


Python Version 
===============

OAuth-Sidecar is built with the latest Python 3 version, supporting only Python3.6 and newer, and uses Docker to create, build and run its image.

Dependencies 
============

These distributions (described in the ``requirements.txt`` file) will be installed automatically when building the Dockerfile. 

* `Flask <http://flask.pocoo.org/docs/1.0/>`_ (version 1.0.2) - a `micro` framework written in Python
* `Flask-Cors <https://flask-cors.readthedocs.io/en/latest/>`_  (version 3.0.7) - a Flask extension that handles Cross Origin Resource Sharing (CORS)
* `Flask-Rauth <https://flask-rauth.readthedocs.io/en/latest/>`_ (version 0.1) - a Flask extension that enables the interaction with OAuth 2.0, OAuth 1.0 and Ofly
* `Gunicorn <http://docs.gunicorn.org/en/stable/index.html>`_ (version 19.9.0) - a light and speedy Python WSGI HTTP server for UNIX, compatible with various web frameworks 

Building the Docker image
=========================

Inside the main folder (where the ``Dockerfile`` is located) run

    ``docker build -t oauth-sidecar:latest``

This command will build for you the Docker image inside your machine. `oauth-sidecar` will be the name of the Docker container that you'll run later and you can change the name with whatever you like the most.

Running the Docker image
========================

After building the Docker image, you must run it using the following line

    ``docker run -it oauth-sidecar``

To add the required environment variables (`CLIENT_ID`, `CLIENT_SECRET` and `INTERNAL_BACKEND`) using the command line just run

    ``docker run -it --e CLIENT_ID={CLIENT_ID} --e CLIENT_SECRET={CLIENT_SECRET} --e INTERNAL_BACKEND={INTERNAL_BACKEND} oauth-sidecar``