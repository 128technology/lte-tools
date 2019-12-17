# change_pin.py

change_pin.py is a tool to manage PIN protected SIM cards to be used with LTE/UMTS modems.

## Install

Just download the file using curl or wget:

```
$ curl -O https://raw.githubusercontent.com/128technology/lte-tools/master/change_pin/change_pin.py
$ chmod +x change_pin.py
$ sudo mv change_pin.py /usr/local/sbin
```

## Usage

```
usage: change_pin.py [-h] [--modem MODEM] [--modem-info] [--disable] [--reset]
                     [--debug] [--verbose]

Change PIN of a SIM card via UMTS/LTE modem

optional arguments:
  -h, --help            show this help message and exit
  --modem MODEM, -m MODEM
                        Location of UMTS/LTE device file
  --modem-info          Print modem info and exit
  --disable, -d         Disable PIN instead of changing it
  --reset               Reset the modem
  --debug               Enable debugging
  --verbose, -v         Show additional information
```

## Disabling PIN of a SIM Card

In most cases LTE/UMTS routers expect SIM cards to be *not* PIN protected.

First disable the PIN:

```
$ change_pin.py --disable
```

Then verify whether PIN has been disabled:

```
$ change_pin.py --modem-info
----- Modem details -----
Quectel
EG25
Revision: EG25GGBR07A07M2G
--------------------------
INFO: CCID: 89490200000000000000 (Provider: T-Mobile Germany)
INFO: Remaining verification attempts: PIN=3 | PUK=10
INFO: PIN verification is disabled
```

Please keep in mind that you need the current PIN to enable PIN verification again.

## Modem Device Selection

By default the script presumes `/dev/ttyUSB2` to be the modem's device file.

In case your modem uses a different device file, you can specify its location by `--modem` or `-m` respectively.

Use `--modem-info` to see details about the modem in use.

## Additional Modems Specs

This scripts has built-in support for these modems:

* Sierra Wireless MC7455
* Quectel EC25/EG25

In case you want to add support for your modem, create a file named `modem_info.json` and copy it to the current working directory.

The file needs to follow this schema:

```
$ cat modem_info.json
{
	"FOOBAR": {
            "vendor_ati": "Foo Bar Inc.",
            "model_ati": "F008AR",
            "reset_command": "AT!RESET",
            "ccid_command": "AT+CCID"
        }
}
```