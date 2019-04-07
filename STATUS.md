# ToDo

## Task #1 ##
* script
  * contemplate fixing 'really big bug' never clearing old cache entries

## Task #2 ##
* fixup vagrantfile to utilize puppet provisioner to configure box
  * use puppet agent to setup host
  ### Tasks ###
  * install python-requests (from OS)
  * ensure date and time are accurate
  * download and start temperature_cacher.py
    * api key will be tricky. local non-checked in hiera perhaps?
* document REST API

# Completed

## Task #1 ##
* setup github repo
* script
  * queries external API for live results
  * caches temperature results, only using if 5m or less old
  * make temperature_cacher an HTTP API
    * ensure GET method
* make sure to add a copy of the DB to repo

## Task #2 ##
* setup vagrant to start usable VM
  * installed puppet 6 i386 for CentOS 6 on this CentOS 7 host via shell
    provisioner. This seemed to the most expedient way to satisfy:
    * running recent CentOS
    * running 32 bit, so vagrant can be ran inside virtualbox instance
    * have a recent version of puppet installed.
    There may have been better methods, I tried a few w/o success. Time...
* setup vagrant networking (ensure vagrant host can reach API)

# Family, oncall, or Extra Credit

## Completed ##
* script:
  * prep for use to allow for location in request query

## Maybe ##
* script:
  * implement api allowing for location in request query

## Maaaaaybe ##
* use puppet provisioner to deploy and configure PostgreSQL (easy)
* script:
  * switch to PostgreSQL (maybe easy?)

