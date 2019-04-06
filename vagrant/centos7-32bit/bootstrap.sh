#!/bin/bash

# obtain pdx-temp.py and start it
curl -o- https://raw.githubusercontent.com/rake74/nwea-pdx-temp/master/python/pdx-temp.py

#TODO add md5sum check here

/usr/bin/python pdx-temp.py
