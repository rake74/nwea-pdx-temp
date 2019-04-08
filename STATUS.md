# ToDo

## Task #1
### Done!

## Task #2
### Done!

# Completed

## Task #1
* setup github repo
* script
  * queries external API for live results
  * caches temperature results, only using if 5m or less old
  * make temperature_cacher an HTTP API
    * ensure GET method
  * contemplate fixing 'really big bug' never clearing old cache entries
  This will not be done as it would prevent examination of the sqlite db.
* make sure to add a copy of the DB to repo

## Task #2
* setup vagrant to start usable VM
  * installed puppet 6 i386 for CentOS 6 on this CentOS 7 host via shell
    provisioner. This seemed to the most expedient way to satisfy:
    * running recent CentOS
    * running 32 bit, so vagrant can be ran inside virtualbox instance
    * have a recent version of puppet installed.
    There may have been better methods, I tried a few w/o success. Time...
* setup vagrant networking (ensure vagrant host can reach API)
* setup vagrantfile to utilize puppet provisioner to configure box
  * use puppet agent to setup host
    * install python-requests (from OS)
    * ensure date and time are accurate
    * download and start temperature_cacher.py
      * handled api by putting it into hiera (dummy value checked in)
* document REST API. Ask the internet what this means, and you will find the
answer you seek - whatever it might be. For this challenge, I felt a human sort
of documentation was best.

# Family, oncall, or Extra Credit (end of spring break, three outages, evaluation challenge)

## Completed ##
* script:
  * prep for use to allow for location in request query
  * implement api allowing for location in request query
  * not listed in challenge, but script is prepped to be tweaked to support
specifying preferred temperature units.

## Maaaaaybe ##
* use puppet provisioner to deploy and configure PostgreSQL (easy)
* script:
  * switch to PostgreSQL (maybe easy?)

These will not be happening. I spent the vast majority of this challenge learning
just enough about Python and Vagrant to complete this task. The time I spent on
puppet, and considering how to deploy, doesn't begin to compare.
