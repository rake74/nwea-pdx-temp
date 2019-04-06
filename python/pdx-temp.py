#!/usr/bin/python

"""
Author: Chris Jacobs

Created as a demo challenge requested by NWEA

Written for python 2.7.5 'as ships' with CentOS 7 32bit for ease of deployment
even if running inside a vagrant box itself running inside a vagrant instance.

# Design requirements:

* Respond to only:
  * GET requests
  * requests to endpoint /temperature
  with the current PDX temperature
* Respond with JSON:
  { "query_time": "[timestamp]", "temperature": "[temperature]" }
* If the last request was greater than 5 minutes ago, return cached value.
* Save cached value in SQLite DB.
* Should be runnable inside a vagrant box, and configured via Puppet provisioner.

# Implementation details

* Use libraries SocketServer and SimpleHTTPServer to implement listener
  I am aware python does not recommend this for production use, but as a first
  go at creating an HTTP API via Python I am running with it. For production
  I would certainly suggest more research and implementation for an acceptable
  'production' use Python HTTP library.
* Listen on port 8080 (for convenience > 1024)
* Use library Requests to obtain temperature from configured source
* Use library PySQLite to cache temperature
* Use library time to get current epoch time

# Further notes:
I did not come up with all the code below in a clean room; I relied on
identifying methods to accomplish the various tasks. When code has been
sourced from another location, I will indicate so.
"""

import SocketServer
import SimpleHTTPServer
import re

import sqlite3
from sqlite3 import Error

import time

# -----------------------
# Statics / defaults
# -----------------------
sqlite_db_file = './temperature.sqlite'
# API information - https://www.weather.gov/documentation/services-web-api
temperature_source_api = https://api.weather.gov
temperature_source_key = 'rake74@gmail.com_for_NWEA_code_challenge'

def create_sqlite_connection(db_file):
    # http://www.sqlitetutorial.net/sqlite-python/create-tables/
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        conn.close()

def create_sqlite_table(conn, create_sqlite_table_sql):
    # http://www.sqlitetutorial.net/sqlite-python/create-tables/
    """ create a table from the create_sqlite_table_sql statement
    :param conn: Connection object
    :param create_sqlite_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_sqlite_table_sql)
    except Error as e:
        print(e)

def get_temperature()
    # TODO
    # query DB for most recent temp
    # if greater then 5 minutes ago, obtain from source API, and save to db

def main()
    #TODO
    # start_listener here

if __name__ == "__main__":
    main()
