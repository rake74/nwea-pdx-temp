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
* Use library requests to obtain temperature data
* Use library json to return, and obtain temperature data
* openweathermap api key is required as first argument
  There's certainly better ways to do this, or managing an api key.
  As no data source nor api key were provided, I signed up for one.
* Temperature is saved and managed in kelvin, converted to fahrenheit when
  returning data.
* location is tracked - in the hopes I get to extra credit

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
import requests
import json

# -----------------------
# Statics / defaults
# -----------------------

sqlite_db_file = "./temperature.sqlite"
# API information - https://openweathermap.org/current
temperature_source_api = "https://api.openweathermap.org/data/2.5/weather"
temperature_source_key = sys.argv[0]
location="Portland, OR, USA"

# -----------------------
# functions
# -----------------------

def create_sqlite_connection(db_file):
    # http://www.sqlitetutorial.net/sqlite-python/create-tables/
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return None

def init_sqlite_table(conn, create_sqlite_table_sql):
    # http://www.sqlitetutorial.net/sqlite-python/create-tables/
    """ create a table from the create_sqlite_table_sql statement
    :param conn: Connection object
    :param create_sqlite_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        cur = conn.cursor()
        cur.execute(create_sqlite_table_sql)
    except Error as e:
        print(e)

def save_temperature_to_sqlite():
    #TODO

def get_temperature_from_sqlite():
    #TODO
    now = int(time.time())

def get_location_from_sqlite(conn,location):
    # inspiration/modeling
    # http://www.sqlitetutorial.net/sqlite-python/sqlite-python-select/
    query = "SELECT lat_long from location WHERE location=" + location
    c = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    return rows

def get_temperature_from_source():
    # light inspiration:
    # https://www.geeksforgeeks.org/python-find-current-weather-of-any-city-using-openweathermap-api/
    # expects source to return json
    # failure to obtain temperature will return 0, which is theoretical only
    # will return lat_lon, and kelvin, and an error if one occurred
    source_query = "?appid=" + temperature_source_key + "&q=" + location
    source_url = temperature_source_api + source_query
    retval = dict();
    retval['lat_long'] = '0,0'
    retval['kelvin'] = 0
    try:
        source_response = requests.get(source_url)
    except:
        retval['error'] = 'failed to get data'
        return retval
    try:
        source_response_json = source_response.json()
    except:
        retval['error'] = 'failed to parse or convert to json/dict'
        return retval
    if source_response_json["cod"] is not 200:
        retval['error'] = 'httpd code is not 200: ' + source_response_json["cod"]
        return retval
    try:
        retval['kelvin'] = int(source_response_json["main"]["temp"])
    except:
        retval['error'] = 'temp not available, perhaps data source format change'
        return retval
    try:
        lat = str(source_response_json["coord"]["lat"])
        lon = str(source_response_json["coord"]["lon"])
        retval['lat_long'] = lat + "," + lon
    except:
        retval['error'] = 'coords not available, perhaps data source format change'
        return retval
    return retval

def get_temperature(conn,location):
    # query DB for most recent temperature for location
    # if greater then 5 minutes ago, obtain from source API, and save to db
    # cleanup location, e.g.: "Portland, OR , USA" becomes "Portland,OR,USA"
    location=re.sub(
                r'[ ]*,[ ]*',
                ','
                location)
    # check db for location, if not present, it's not cached
    # TODO

def main():
    #TODO
    conn = create_sqlite_connection(sqlite_db_file)
    sql_init_temperature_db = """
        CREATE TABLE IF NOT EXISTS temperature(
            timestamp integer PRIMARY KEY,
            lat_long  text NOT NULL,
            kelvin    integer
        ); """
    init_sqlite_table(conn,sql_init_temperature_db)
    sql_init_location_db = """
        CREATE TABLE IF NOT EXISTS location(
            lat_long    text PRIMARY KEY,
            description text NOT NULL,
        ); """
    init_sqlite_table(conn,sql_init_location_db)
    # start_listener here
    # but instead:
    # iterative deving, not listening, just call from command line for now
    current_temperature = get_temperature(conn,location)
    print (current_temperature)

if __name__ == "__main__":
    main()
