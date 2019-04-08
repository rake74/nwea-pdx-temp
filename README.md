# Temperature Cacher

This provides a caching API to query openweathermap.org for city temperature.  
Cached values are ignored after five minutes.

To use this, you must meet these pre-requisites:
* vagrant installed running on a 64 bit host
* a functioning internet connection to download resources
* an openweathermap.org API key (see: https://openweathermap.org/api)

## How to deploy ##

1. First, you must obtain the contents of the vagrant directory.
    * Using **git**, download the repo:  
  `git clone https://github.com/rake74/nwea-pdx-temp.git`  
  Then feel free to move the vagrant dir where convenient.
    * Using **svn**, you may download just the vagrant dir:  
  `svn export https://github.com/rake74/nwea-pdx-temp/trunk/vagrant`
2. Replace dummy value for apikey with your openweathermap.org API key in file `puppet/hiera/common.yaml`.  
  Current setting is:  
  `temperature_cacher::apikey: 'get your API key at https://openweathermap.org/api'`
3. While in the vagrant directory, run `vagrant up`

The Vagrantfile will install puppet, and then use it to complete the build, setup and start the temperature_cacher service.

Per Vagrantfile config, the API will be avilable to the vagrant host, and the vagrant box at `http://127.0.0.1:8080/temperature`.

### Making changes to running deployed box ###

If you make changes to the puppet code, including the server script, you may implement them immediately via:  
`vagrant provision --provision-with puppet`

## API Documentation ##

The API only supports the GET http method.  
The API only supports the endpoint `/temperature`  
The API returns JSON following format (formatted nicely here for human readability):
```
{  
   "query_time":UNIXTIME,
   "temperature":FAHRENHEIT,
   "cached_result":"true|false"
}
```
Real example:
```
{  
   "query_time":1554713410,
   "temperature":42,
   "cached_result":"true"
}
```
You may specify the city by adding the query parameter `city=CITYNAME`  
The default city is Portland, OR, USA.  
This parameter is ultimately interpreted by openweathermap.org API:
* urlencode the cityname (if necessary)  
* Many cities share names. If you attempt to specify a state or provence, you must also specify the country.
* Not all cities are supported.

Examples API calls:
* `curl http://127.0.0.1:8080/temperature`
* `curl http://127.0.0.1:8080/temperature?city=Honolulu`
* `curl http://127.0.0.1:8080/temperature?city=Boston,MA,USA`
* `curl http://127.0.0.1:8080/temperature?city=New+York`
