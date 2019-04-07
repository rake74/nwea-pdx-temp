# ToDo

## Task #1 ##
* script
  * make temperature_cacher an HTTP API
    * ensure GET method
  * contemplate fixing 'really big bug' never clearing old cache entries
* make sure to add a copy of the DB to repo

## Task #2 ##
* setup vagrant networking (ensure vagrant host can reach API)
* fixup vagrantfile to utilize puppet provisioner to configure box
  * use puppet provisioner to setup host
* document REST API

# Completed

## Task #1 ##
* setup github repo
* script
  * queries external API for live results
  * caches temperature results, only using if 5m or less old

## Task #2 ##
* setup vagrant to start usable VM

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

