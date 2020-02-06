# lte\_volume\_info.py

lte\_volume\_info.py retrieves data from connected router nodes of a 128T conductor and generates an html file providing a summary of used LTE volume quota.

## Install

```
$ dnf install -y git
$ git clone https://github.com/128technology/lte-tools.git
$ cd lte-tools/lte_volume_info
$ cp 128t_black.png t128.woff /var/www/128technology/
```

## Usage

```
usage: lte_volume_info.py [-h] [--cache-dir CACHE_DIR] [--html-path HTML_PATH]
                          [--config-path CONFIG_PATH]
                          [--percentage-orange PERCENTAGE_ORANGE]
                          [--percentage-red PERCENTAGE_RED]

Retrieve LTE volume stats and generate html document.

optional arguments:
  -h, --help            show this help message and exit
  --cache-dir CACHE_DIR
                        path to stats cache
  --html-path HTML_PATH
                        path to html document
  --config-path CONFIG_PATH
                        path to 128T config
  --percentage-orange PERCENTAGE_ORANGE
                        show bar as orange if percentage > X
  --percentage-red PERCENTAGE_RED
                        show bar as red if percentage > X
```

After running `lte_volume_info.py` an html document `/var/www/128technology/lte_volume_info.html` will be created which can be loaded from the conductors webserver: `https://<conductor-address>/lte_volume_info.html`

## Customizations
The html file is generated based on the template file `lte_volume_info.template`.
The format of this template is jinja2, so customizations can be performed using html and jinja2 syntax.