# haproxy-galera
MariaDB Galera health check script for HAProxy

## Installation

Copy `main.py` to `/usr/local/sbin/haproxy-galera` and `chmod +x`.

### Dependencies

Requires `python-mysqldb`, and `python-requests` installed.

### Systemd

Copy the included systemd unit file `haproxy-galera.service` to `/etc/systemd/system/`.

## Usage

### MariaDB Setup

Create a local user to connect and check status:

```mysql
CREATE USER 'haproxy'@'localhost';
```

### HAProxy Setup

```
listen MYSQL
    bind 0.0.0.0:3306
    mode tcp
    option tcplog
    option httpchk
    balance leastconn
    default-server port 3305 inter 2s downinter 5s rise 3 fall 1 maxconn 128 maxqueue 128 weight 100 slowstart 60s
    server db1 192.168.22.141:3306 check
    server db2 192.168.22.142:3306 check backup
    server db3 192.168.22.143:3306 check backup
```
