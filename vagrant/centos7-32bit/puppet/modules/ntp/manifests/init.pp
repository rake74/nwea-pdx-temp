# setup ntpd to keep time up to date

class ntp {

  package{['ntp','ntpdate']:
    ensure => installed,
    notify => Exec['force-ntpd-sync-now'],
  }

  exec{'force-ntpd-sync-now':
    command     => 'systemctl stop ntpd; ntpd -qg; systemctl start ntpd',
    path        => '/sbin:/bin:/usr/sbin:/usr/bin',
    refreshonly => true,
    logoutput   => true,
  }

  service {'ntpd':
    ensure  => 'running',
    enable  => 'true',
    require => Package['ntp'],
  }

}
