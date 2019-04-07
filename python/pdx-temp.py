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
* location is tracked - in the hopes I get to the extra credit item

# Further notes:
I did not come up with all the code below in a clean room; I relied on
identifying methods to accomplish the various tasks. When code has been
sourced from another location, I will indicate so.
But to get really real, this is my third time diving into a python script, so
we all know I looked up format or 'how to do X in python' for a lot of this.

# Potential issues (within scope of challenge)
* db connection is never closed.
* old temperatures are never cleaned. db could eat the disk, quickly in prod.
"""

import SocketServer
import SimpleHTTPServer
import re
import sys

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
temperature_source_key = sys.argv[1]

# these may be used to enable location or output scale per user query
location="Portland, OR, USA"
# location="Seattle, WA, USA"
temperature_scale="fahrenheit"

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
        cursor = conn.cursor()
        cursor.execute(create_sqlite_table_sql)
    except Error as e:
        print(e)

def save_temperature_to_sqlite(conn,now,location,source_data):
    cursor = conn.cursor()
    lat_long = str(source_data['lat_long'])
    kelvin = int(source_data['kelvin'])
    # add data to temperature table
    insert = """INSERT INTO temperature(timestamp, lat_long, kelvin)
                VALUES (?,?,?)"""
    try:
        cursor.execute(insert,(now,lat_long,kelvin))
        conn.commit()
    except Error as e:
        print(e)
    # add location data to location table... if it's not already present
    check_location = """select lat_long, description FROM location
       WHERE lat_long = '%s'
       AND   description='%s'""" %(lat_long,location)
    cursor.execute(check_location)
    check_location_rows=cursor.fetchall()
    if len(check_location_rows) is 0:
        insert = """INSERT INTO location(lat_long, description)
                    VALUES (?,?)"""
        try:
            cursor.execute(insert,(lat_long,location))
            conn.commit()
        except Error as e:
            print(e)

def get_temperature_from_source(location):
    # (now very) light inspiration:
    # https://www.geeksforgeeks.org/python-find-current-weather-of-any-city-using-openweathermap-api/
    # this expects source to return json
    # failure to obtain temperature will return 0, which is theoretical only
    # will return lat_long, and kelvin, and an error if one occurred
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
        retval['error'] = 'httpd code is not 200: ' + str(source_response_json["cod"])
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
    retval['error'] = ''
    return retval

def kelvin_to_x(kelvin):
    try:
        kelvin=int(kelvin)
    except:
        return 666  # rely on user to let us know for now I s'pose
    # default to fahrenheit because it's what my parents used
    if (temperature_scale == 'k' or temperature_scale == 'kelvin'):
        return int(kelvin)
    if (temperature_scale == 'c' or temperature_scale == 'celsius'):
        return int(kelvin-273.15)
    return int((kelvin-273.15)*9/5+32)

def get_temperature(conn,location):
    # query DB for most recent temperature for location
    # if greater then 5 minutes ago, obtain from source API, and save to db
    # cleanup location, e.g.: "Portland, OR , USA" becomes "Portland,OR,USA"
    now = int(time.time())
    max_timestamp = now - ( 5 * 60 )
    # check for cached data
    #   no matter the location used, lat-long, city name, etc., querying for
    #   that location will return the same data.
    #   data from upstream provider includes lat and long in response so cache
    #   using that.
    cached_query = """
        SELECT   kelvin
        FROM     temperature 
        WHERE    timestamp >= %s 
        AND      lat_long IN 
                 ( 
                        SELECT lat_long 
                        FROM   location 
                        WHERE  description = '%s') 
        ORDER BY timestamp DESC
        LIMIT 1""" %(max_timestamp,location)
    cursor = conn.cursor()
    cursor.execute(cached_query)
    cached_result = cursor.fetchall()
    retval = dict();
    retval['query_time'] = now
    if len(cached_result) is not 0:  # valid cache
        retval['cached_result'] = 'true'
        temperature = cached_result[0]
    else:                            # no valid cache
        retval['cached_result'] = 'false'
        source_data = get_temperature_from_source(location)
        if source_data['error'] is not '':
            retval['temperature'] = 0
            retval['error'] = source_data['error']
            return retval
        else:
            temperature = source_data['kelvin']
            save_temperature_to_sqlite(conn,now,location,source_data)
    retval['temperature'] = kelvin_to_x(temperature)
    return retval

def init_sqlite3_db():
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
            id          integer PRIMARY KEY, 
            lat_long    text NOT NULL,
            description text NOT NULL
        ); """
    init_sqlite_table(conn,sql_init_location_db)
    return conn

def main(location):
    conn = init_sqlite3_db()
    # cleanup described location
    location=re.sub(
                r'[ ]*,[ ]*',
                ',',
                location)
    location=location.lower()
    # start_listener here
    # but instead:
    # iterative deving, not listening, just call from command line for now
    results = get_temperature(conn,location)
    print (results)

if __name__ == "__main__":
    main(location)
