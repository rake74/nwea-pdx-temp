# prep and start temperature_cacher

class temperature_cacher ( String $apikey = 'no default apikey from class') {

  include temperature_cacher::base_setup
  include temperature_cacher::init_setup

  Class['temperature_cacher::base_setup']
  ~> Class['temperature_cacher::init_setup']

}
