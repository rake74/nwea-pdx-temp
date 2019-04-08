# setup user, dir, files

class temperature_cacher::base_setup {

  $apikey = $::temperature_cacher::apikey

  package{'python-requests':
    ensure => installed,
  }

  group{'temperature_cacher':
    ensure     => present,
    forcelocal => true,
  }
  user{'temperature_cacher':
    ensure     => present,
    groups     => 'temperature_cacher',
    forcelocal => true,
  }

  File{
    owner  => 'temperature_cacher',
    group  => 'temperature_cacher',
    mode   => '0755',
    notify => Exec['self_test-temperature_cacher.py'],
  }

  file{
    '/opt':
      ensure => directory,
      owner  => 'root',
      group  => 'root',
    ;
    '/opt/temperature_cacher':
      ensure => directory,
      mode   => '2775',
    ;
    '/opt/temperature_cacher/temperature_cacher.py':
      ensure => present,
      source => 'puppet:///modules/temperature_cacher/temperature_cacher.py',
    ;
    '/opt/temperature_cacher/temperature_cacher.apikey':
      content   => $apikey,
      show_diff => false,
      mode      => '0440',
  }

  exec{'self_test-temperature_cacher.py':
    command     => '/opt/temperature_cacher/temperature_cacher.py test nocache',
    cwd         => '/opt/temperature_cacher',
    refreshonly => true,
  }

}
