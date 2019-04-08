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
* I did not come up with all the code below in a clean room; I relied on
  identifying methods to accomplish the various tasks. When code has been
  sourced from another location, I will indicate so.
  But to get really real, this is my third time diving into a python script, so
  we all know I looked up format or 'how to do X in python' for a lot of this.
* argument handling: I know how to do arguments in python 2 and 3, and support
  both in a single script. However, for this challenge, and to conserve time
  I'm keeping things simple.
  TL;DR: yes, the argument handling here is lame.

# Potential issues (within scope of challenge)
* db connection is never closed.
* old temperatures are never cleaned. db could eat the disk, quickly in prod.
"""

#import SocketServer
#import SimpleHTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import re
import sys
import os

import sqlite3
from sqlite3 import Error

import time
import requests
import json
from urlparse import urlsplit,parse_qs
from pprint import pprint

# -----------------------
# Statics / defaults
# -----------------------
sqlite_db_file = "./temperature_cacher.sqlite"
# API information - https://openweathermap.org/current
port = 8080
temperature_source_api = "https://api.openweathermap.org/data/2.5/weather"

try:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    apikey_file = open(dir_path+"/temperature_cacher.apikey", "r")
    temperature_source_key = apikey_file.readline().rstrip()
    apikey_file.close
except Error as e:
    sys.exit("API key file required: temperature_cacher.apikey\n" + e) 

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
    except Error as e:
        return e # rely on user to let us know for now I s'pose
    # default to fahrenheit because it's what my parents used
    if (temperature_scale == 'k' or temperature_scale == 'kelvin'):
        return int(kelvin)
    if (temperature_scale == 'c' or temperature_scale == 'celsius'):
        return int(kelvin-273.15)
    return int((kelvin-273.15)*9/5+32)

def get_temperature(conn,location,usecache='true'):
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
    if usecache is 'true':
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
    else:
        cached_result = dict()
    retval = dict()
    retval['query_time'] = now
    if len(cached_result) is not 0 and usecache is 'true': # use cache
        retval['cached_result'] = 'true'
        temperature = cached_result[0][0]
    else:                            # no valid cache
        retval['cached_result'] = 'false'
        source_data = get_temperature_from_source(location)
        if source_data['error'] is not '':
            retval['temperature'] = 0
            retval['error'] = source_data['error']
            return retval
        else:
            temperature = source_data['kelvin']
            if usecache is 'true':
                save_temperature_to_sqlite(conn,now,location,source_data)
    retval['temperature'] = kelvin_to_x(temperature)
    #return retval
    return json.dumps(retval)

def init_sqlite3_db():
    conn = create_sqlite_connection(sqlite_db_file)
    sql_init_temperature_db = """
        CREATE TABLE IF NOT EXISTS temperature(
            id        integer PRIMARY KEY,
            timestamp integer,
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

def method_not_allowed(req):
    req.send_response(405)
    req.finish()
    req.connection.close()

# class required by HTTPServer
class api_handler(BaseHTTPRequestHandler):
    # inspiration/starting points
    # http://dwightreid.com/blog/2017/05/22/create-web-service-python-rest-api/
    # https://gist.github.com/bradmontgomery/2219997
    # cut to BaseHTTPRequestHandler w/ mild assistance from
    # https://gist.github.com/trungly/5889154
    def do_GET(self):
        url_split = urlsplit(self.path)
        path = url_split.path
        # only responde to /temperature endpoint
        if path != '/temperature':
            self.send_response(403)
            self.send_header("Content-type","application/json")
            self.end_headers()
            self.wfile.write({'invalid path': path})
            self.finish()
            self.connection.close()
            return
        query = parse_qs(url_split.query)
        if 'city' in query:
            my_location = str(query['city'][0])
        else:
            my_location = str(location)
        my_location=re.sub(
                    r'[ ]*,[ ]*',
                    ',',
                    my_location)
        my_location=my_location.lower()
        conn = create_sqlite_connection(sqlite_db_file)
        results = get_temperature(conn,my_location)
        if "error" in results:
            retcode = 500
        else:
            retcode = 200
        self.send_response(retcode)
        self.send_header("Content-type","application/json")
        self.end_headers()
        self.wfile.write(results)
        self.finish()
        self.connection.close()
        return
    def do_PUT(self):
        method_not_allowed(self)
    def do_POST(self):
        method_not_allowed(self)
    def do_DELETE(self):
        method_not_allowed(self)
    def do_CONNECT(self):
        method_not_allowed(self)
    def do_OPTIONS(self):
        method_not_allowed(self)
    def do_TRACE(self):
        method_not_allowed(self)
    def do_PATCH(self):
        method_not_allowed(self)

def main(location,port):
    conn = init_sqlite3_db()
    # cleanup described location
    location=re.sub(
                r'[ ]*,[ ]*',
                ',',
                location)
    location=location.lower()
    # run self test using oddball location
    self_test = get_temperature(conn,'grytviken,gs','false')
    if 'error' in self_test:
        print(self_test)
        sys.exit(1)

    # if test is an arg, run and exit sans listener
    if 'test' in sys.argv:
        if 'nocache' in sys.argv:
            results = get_temperature(conn,location,'false')
        else:
            results = get_temperature(conn,location)
        print (results)
        if 'error' in results:
          sys.exit(1)
        sys.exit()
    # start_listener here
    httpd = HTTPServer(('', port), api_handler)
    print "serving at port", port
    httpd.serve_forever()

if __name__ == "__main__":
    main(location,port)
