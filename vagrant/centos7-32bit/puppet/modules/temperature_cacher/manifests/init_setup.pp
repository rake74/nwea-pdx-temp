# sets up init, assumed for systemd - tested on CentOS 7

class temperature_cacher::init_setup {

  file{'/lib/systemd/system/temperature_cacher.service':
    ensure  => present,
    source  => 'puppet:///modules/temperature_cacher/temperature_cacher.service',
    notify  => Exec['temperature_cacher-reload-systemd'],
  }~>
  exec{'temperature_cacher-reload-systemd':
    command     => 'systemctl daemon-reload',
    path        => '/usr/bin:/bin:/usr/sbin',
    refreshonly => true,
  }

  service {'temperature_cacher.service':
    ensure  => running,
    enable  => true,
    require => File['/lib/systemd/system/temperature_cacher.service'],
  }

}
