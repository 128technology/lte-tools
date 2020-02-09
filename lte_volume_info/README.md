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

## Configuration
On a 128T router it is recommended to create a dedicated service and service route to make sure the provider's API can be reached through the LTE network interface.

```
config
    authority
        tenant   128t-management
            name         128t-management
            description  "Tenant for router management traffic"
        exit
        service  pass_telekom_de
            name                  pass_telekom_de
            transport             tcp
                protocol    tcp
                port-range  80
                    start-port  80
                exit
            exit
            address               109.237.176.33
            access-policy         128t-management
                source  128t-management
            exit
            share-service-routes  false
        exit
    exit
exit
```
To allow linux processes on the router (e.g. `curl`) reaching the API, a loopback interface is required. Traffic which enters this interface shall be assigned to tenant `128t-management`:

```
router   lte-router
    name           lte-router
    node           lte-router-node
        name              lte-router-node
        device-interface  Loopback
            name               Loopback
            type               host
            network-interface  Loopback
                name               Loopback
                default-route      true
                tenant             128t-management
                source-nat         true
                management-vector
                    priority  200
                exit
                address            169.254.20.1
                    ip-address     169.254.20.1
                    prefix-length  30
                    gateway        169.254.20.2
                exit
            exit
        exit
    exit
exit
```
Finally, the service-routes instructs the routing engine to forward traffic to the API service `pass_telekom_de` over LTE:

```
router   lte-router
    name           lte-router
    node           lte-router-node
        name              lte-router-node
    service-route  pass_telekom_de
        name          pass_telekom_de
        service-name  pass_telekom_de
        next-hop      lte-router-node LTE
            node-name  lte-router-node
            interface  LTE
        exit
    exit
exit
```

## Customizations
The html file is generated based on the template file `lte_volume_info.template`.
The format of this template is jinja2, so customizations can be performed using html and jinja2 syntax.