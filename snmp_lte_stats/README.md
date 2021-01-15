# snmp\_lte\_stats.py

snmp\_lte\_stats.py is a script to extend the snmpd capabilities to provide lte related statistics via SNMP.

## Clone Repo

```
$ sudo dnf install -y git
$ cd /usr/local/src
$ sudo git clone https://github.com/128technology/lte-tools.git
$ cd /srv/salt
$ sudo ln -s /usr/local/src/lte-tools/snmp_lte_stats/snmp_lte.sls
$ sudo ln -s /usr/local/src/lte-tools/snmp_lte_stats/snmp_lte_stats.py
```

## Apply salt state

The salt state `snmp\_lte.sls` needs to be referenced in the `top.sls` file, e.g.

```
$ cat /srv/salt/top.sls
base:
  'test-router':
    - snmp_lte
```

On the conductor run state.apply to install the extension on "test-router":

```
$ sudo t128-salt test-router state.apply saltenv=base
```
