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

* Use BaseHTTPServer to implement listener
* Listen on port 8080 (for convenience > 1024)
* Use library Requests to obtain temperature from configured source
* Use library PySQLite to cache temperature
* Use library time to get current epoch time
* Use library requests to obtain temperature data
* Use library json to return, and obtain temperature data
* Use library urllib to quote encode location when querying source
* Use library urlparse to parse request from user
* openweathermap api key is required in hiera
* Temperature is saved and managed in kelvin, converted to fahrenheit when
  returning data. Enabled future improvement for user to set returned temp scale
* location is tracked as lat_long in temperature cache/db, lat_long and user
  provided city description are tracked in location cache/db.

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
import urllib

# -----------------------
# Statics / defaults
# -----------------------
sqlite_db_file = "/opt/temperature_cacher/temperature_cacher.sqlite"
port = 8080
default_location = "Portland, OR, USA"
# default_location = "Seattle, WA, USA"
temperature_scale = "fahrenheit"
# API information - https://openweathermap.org/current
temperature_source_api = "https://api.openweathermap.org/data/2.5/weather"
try:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    apikey_file = open(dir_path+"/temperature_cacher.apikey", "r")
    temperature_source_key = apikey_file.readline().rstrip()
    apikey_file.close
except Error as e:
    sys.exit("API key file required: temperature_cacher.apikey\n" + e) 

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

def save_temperature_to_sqlite(conn,now,description,fresh_data):
    """
    Cache time, lat_long, and temperature to temperature table
    Cache description for lat_long to location table
    """
    cursor = conn.cursor()
    lat_long = str(fresh_data['lat_long'])
    kelvin = int(fresh_data['kelvin'])
    # add data to temperature table
    insert = """
        INSERT INTO temperature
                    (timestamp, lat_long, kelvin)
        VALUES      (?,?,?)"""
    try:
        cursor.execute(insert,(now,lat_long,kelvin))
        conn.commit()
    except Error as e:
        print(e)
    # add description and lat_long mapping to location table if not present
    check_description = """
        SELECT lat_long,
               description
        FROM   location
        WHERE  lat_long = '%s'
               AND description = '%s'""" %(lat_long,description)
    cursor.execute(check_description)
    check_description_rows = cursor.fetchall()
    if len(check_description_rows) == 0:
        insert = """
            INSERT INTO location
                        (lat_long,description) 
            VALUES      (?,?)"""
        try:
            cursor.execute(insert,(lat_long,description))
            conn.commit()
        except Error as e:
            print(e)

def get_temperature_from_source(location):
    # (now very) light inspiration:
    # https://www.geeksforgeeks.org/python-find-current-weather-of-any-city-using-openweathermap-api/
    # this expects source to return json
    # failure to obtain temperature will return 0, which is theoretical only
    # will return lat_long, and kelvin, and an error if one occurred
    source_query = "?q=" + urllib.quote(location) + \
                   "&appid=" + temperature_source_key
    source_url = temperature_source_api + source_query
    return_data = dict();
    return_data['lat_long'] = '0,0'
    return_data['kelvin'] = 0
    return_data['source_url'] = source_url
    try:
        source_response = requests.get(source_url)
    except:
        return_data['error'] = 'failed to get data'
        return return_data
    try:
        source_response_json = source_response.json()
    except:
        return_data['error'] = 'failed to parse or convert to json/dict'
        return return_data
    if source_response_json["cod"] != 200:
        return_data['error'] = 'httpd code is not 200: ' + str(source_response_json["cod"])
        return return_data
    try:
        return_data['kelvin'] = int(source_response_json["main"]["temp"])
    except:
        return_data['error'] = 'temp not available, perhaps data source format change'
        return return_data
    try:
        lat = str(source_response_json["coord"]["lat"])
        lon = str(source_response_json["coord"]["lon"])
        return_data['lat_long'] = lat + "," + lon
    except:
        return_data['error'] = 'coords not available, perhaps data source format change'
        return return_data
    return return_data

def kelvin_to_x(kelvin):
    """
    convert kelvin to celsius or fahrenheit. If I missed a scale, should be
    easy to add...
    """
    try:
        kelvin = int(kelvin)
    except Error as e:
        return e # rely on user to let us know for now I s'pose
    # default to fahrenheit because it's what my parents used
    if (temperature_scale == 'k' or temperature_scale == 'kelvin'):
        return int(kelvin)
    if (temperature_scale == 'c' or temperature_scale == 'celsius'):
        return int(kelvin-273.15)
    return int((kelvin-273.15)*9/5+32)

def get_temperature(conn,location,usecache = 'true'):
    """
    query DB for most recent temperature for location
    if greater then 5 minutes ago, obtain from source API, and save to db

    usecache != 'true' will skip _both_ checking and updating the cache.
    """
    # cleanup location
    location = re.sub(
                   r'[ ]*,[ ]*',
                   ',',
                   location)
    location = location.lower()
    # time vars
    now = int(time.time())
    max_timestamp = now - ( 5 * 60 )
    # check for cached data
    #   no matter the location used, lat-long, city name, etc., querying for
    #   that location will return the same data.
    #   data from upstream provider includes lat and long in response so cache
    #   using that.
    if usecache == 'true':                             # check cache
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
        cached_result = list()
    return_data = dict()
    return_data['query_time'] = now
    if len(cached_result) != 0 and usecache == 'true': # use cache result
        return_data['cached_result'] = 'true'
        temperature = cached_result[0][0]
    else:                                              # no valid cache
        return_data['cached_result'] = 'false'
        fresh_data = get_temperature_from_source(location)
        #return_data['fresh_data'] = fresh_data
        if 'error' in fresh_data:
            return_data['temperature'] = 0
            return_data['error'] = fresh_data['error']
            return return_data
        else:
            temperature = fresh_data['kelvin']
            if usecache == 'true':                     # cache new result
                save_temperature_to_sqlite(conn,now,location,fresh_data)
    return_data['temperature'] = kelvin_to_x(temperature)
    #return_data['location'] = location
    return json.dumps(return_data)

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
            my_location = query['city'][0]
        else:
            my_location = default_location
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

def main():
    conn = init_sqlite3_db()
    # run self test using oddball location
    startup_self_test = get_temperature(conn,'grytviken,gs','false')
    if 'error' in startup_self_test:
        #startup_self_test['startup_self_test'] = 'failure'
 	print('startup_self_test failed')
        print(startup_self_test)
        sys.exit(1)

    # if test is an arg, run and exit sans listener using default_location
    if 'test' in sys.argv:
        if 'nocache' in sys.argv:
            results = get_temperature(conn,default_location,'false')
        else:
            results = get_temperature(conn,default_location)
        print (results)
        if 'error' in results:
          sys.exit(1)
        sys.exit()
    # start_listener here
    httpd = HTTPServer(('', port), api_handler)
    print "serving at port", port
    httpd.serve_forever()

if __name__ == "__main__":
    main()
