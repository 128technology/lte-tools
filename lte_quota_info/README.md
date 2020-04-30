# lte\_quota\_info.py

lte\_quota\_info.py retrieves data from connected router nodes of a 128T conductor and generates an html file providing a summary of used LTE quota.

## Install

```
$ dnf install -y git
$ git clone https://github.com/128technology/lte-tools.git
$ cd lte-tools/lte_quota_info
$ cp 128t_black.png t128.woff /var/www/128technology/
$ sudo mkdir /var/lib/128technology/lte_quota_info
$ sudo chown t128 /var/lib/128technology/lte_quota_info
$ sudo touch /var/www/128technology/lte_quota_info.html
$ sudo chown t128 /var/www/128technology/lte_quota_info.html
```

## Usage

```
usage: lte_quota_info.py [-h] [--config CONFIG] [--debug]

Retrieve LTE quota stats and generate html document.

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        config file
  --debug, -d           show debug messages
```

After running `lte_quota_info.py` an html document will be created which can be loaded from the conductors webserver. The location of this file is configured by `html_path` in the config file (see below) (default location: `/var/www/128technology/lte_quota_info.html`) translates to url `https://<conductor-address>/lte_quota_info.html`

## Configuration
The script requires a config file which contains all required parameters. A sample file called `sample_config.json` is part of the git repository. Copy the file and adjust parameters to your runtime environment:

```
$ cp sample_config.json config.json
$ vi config.json
```
* api_key - needed to authenticate to the conductors REST/GraphQL API,
* default_quota or quota per router - needed to show a resonable max. (monthly) quota,

All other parameters can be left at their defaults.

## Cronjob
The script stores samples of received/sent bytes of the LTE device- interfaces from all routers which are connected to a conductor.
To get accurate reported values it is recommended to run the script minutely per cronjob. Keep in mind that counters get reset during router restart. Keeping the interval short helps to keep track of such reset events.

The crontab for a minutely script trigger looks like:

```
* * * * *    python /home/t128/lte-tools/lte_quota_info/lte_quota_info.py -c /home/t128/lte-tools/lte_quota_info/config.json
```

## Customizations
The html file is generated based on the template file `lte_quota_info.template`.
The format of this template is jinja2, so customizations can be performed using html and jinja2 syntax.