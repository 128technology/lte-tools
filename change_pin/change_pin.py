#!/usr/bin/env python
###############################################################################
# Copyright (c) 2019 128 Technology, Inc.
# All rights reserved.
###############################################################################

# This script allows to change/disable/unblock a PIN of SIM cards
# as used in UMTS/LTE modems.

from __future__ import print_function
import argparse
import json
import serial
import sys
import termios
import tty


class ModemException(Exception):
    """Class to handle modem errors."""
    pass


class UnexpectedResponseException(Exception):
    """Class to handle unexpected responses."""
    pass


class Modem:
    """Class to handle modem calls."""
    modem = None
    current_pin = None
    reset_command = 'AT!RESET'
    supported_modem_info = {
        'MC7455': {
            'vendor_ati': 'Manufacturer: Sierra Wireless, Incorporated',
            'model_ati': 'Model: MC7455',
            'vendor': 'Sierra Wireless',
            'pin_retries_command': None,
            'reset_command': 'AT!RESET',
        },
        'EG25': {
            'vendor_ati': 'Quectel',
            'model_ati': 'EG25',
            'pin_retries_command': 'AT+QPINC?',
            'reset_command': 'AT+CFUN=1,1',
        },
    }
    modem_info = supported_modem_info

    def __init__(self, device_name, debug, verbose):
        """Open a device and return handle."""
        self.modem = serial.Serial(device_name, timeout=5)
        self.debug = debug
        self.verbose = verbose

        # Try to read additional modem infos
        modem_info_filename = 'modem_info.json'
        try:
            with open(modem_info_filename) as fd:
                content = json.load(fd)
                self.modem_info.update(content)
        except IOError:
            pass
        except ValueError:
            warning('Modem info database "{}" could not be parsed.'.format(
                modem_info_filename))
        self.detect_model()

    def __del__(self):
        """Destructor."""
        if self.modem:
            self.modem.close()

    def print_debug(self, message):
        """Print debug information."""
        if self.debug:
            debug(message)

    def print_verbose(self, message):
        """Print verbose information."""
        if self.verbose:
            info(message, True)

    def send_command(self, command):
        """Send AT command to modem."""
        self.print_debug('SND: ' + command)
        self.modem.write(b'{}\r'.format(command))

    def get_response(self, max=12):
        """Return AT command response."""
        response = []
        i = 1
        while True:
            if i > max:
                raise UnexpectedResponseException(
                    'No status code in {} response lines'.format(max))

            line = self.modem.readline().strip()
            self.print_debug('RCV: ' + line)
            # exit condition for loop
            if line == 'OK':
                if response and not response[-1]:
                    # remove empty line before 'OK'
                    del(response[-1])
                break
            if '+CME ERROR: SIM not inserted' in line or \
               '+CME ERROR: SIM failure' in line or \
               '+CME ERROR: 10' in line:
                raise ModemException('No SIM inserted? ({})'.format(line))
            if 'ERROR' in line:
                raise ModemException(line)

            # don't echo command
            if i > 1:
                response.append(line)
            i += 1
        return response

    def detect_model(self):
        self.model = None
        self.pin_retries_command = None
        self.send_command('ATI')
        self.ati = self.get_response()
        # Seek modem vendor/model based on output of 'ATI'
        for k, v in self.modem_info.items():
            if v['vendor_ati'] in self.ati:
                self.vendor = v['vendor_ati']
                if 'vendor' in v:
                    self.vendor = v['vendor']
                if v['model_ati'] in self.ati:
                    self.model = k
                    if 'pin_retries_command' in v:
                        self.pin_retries_command = v['pin_retries_command']
                    if 'reset_command' in v:
                        self.reset_command = v['reset_command']
        if self.model:
            self.print_verbose(
                'Detected Modem: {m.vendor} {m.model}'.format(m=self))

    def print_modem_info(self):
        """Print modem info."""
        # show device model (ATI)
        print('----- Modem details -----')
        print('\n'.join(self.ati))
        print('-'*26)
        self.get_pin_attempts()
        self.sim_is_pin_protected()

    def reset(self):
        """Reset Modem."""
        self.send_command(self.reset_command)

    def sim_is_locked(self):
        """Return if SIM is locked (PIN protected)."""
        self.send_command('AT+CPIN?')
        response = self.get_response()
        if response[0] == '+CPIN: READY':
            return False
        if response[0] == '+CPIN: SIM PIN':
            return True

    def sim_is_pin_protected(self):
        """Return if SIM is PIN protected."""
        self.send_command('AT+CLCK="SC",2')
        response = self.get_response()
        if response[0] == '+CLCK: 0':
            self.print_verbose('PIN verification is disabled')
            return False
        if response[0] == '+CLCK: 1':
            self.print_verbose('PIN verification is enabled')
            return True

    def get_pin_attempts(self):
        """Return remaining PIN attempts (if supported)."""
        if self.pin_retries_command:
            self.send_command(self.pin_retries_command)
            for line in self.get_response():
                if '+QPINC: "SC",' in line:
                    pin, puk = line.split(',')[1:3]
                    self.print_verbose(('Remaining verification attempts:'
                                        ' PIN={} | PUK={}').format(pin, puk))

    def unlock_sim(self):
        """Unlock SIM by using PIN."""
        self.get_pin_attempts()
        current_pin = prompt_for_pin('Current PIN')
        if not current_pin:
            return
        self.print_debug('Current PIN: ' + current_pin)
        self.send_command('AT+CPIN="{}"'.format(current_pin))
        self.get_response()
        self.current_pin = current_pin

    def unblock_sim(self):
        """Unblock SIM by using PUK."""
        return None

    def change_pin(self, enabled=True):
        """Change PIN of a SIM."""
        if not self.current_pin:
            current_pin = prompt_for_pin('Current PIN')
            self.print_debug('Current PIN: ' + current_pin)

        # prompt for new PIN
        new_pin1 = prompt_for_pin('New PIN')
        new_pin2 = prompt_for_pin('Retype new PIN')
        if new_pin1 != new_pin2:
            error('New PINs do not match')
            return
        self.print_debug('New PIN: ' + current_pin)

        # Set new PIN
        if not enabled:
            # PIN needs to be enabled first
            self.send_command('AT+CLCK="SC",1,"{}"'.format(current_pin))
            self.get_response()

        self.send_command('AT+CPWD="SC","{}","{}"'.format(
            current_pin, new_pin1))
        self.get_response()

    def disable_pin(self):
        """Disable PIN of a SIM."""
        if not self.current_pin:
            current_pin = prompt_for_pin('Current PIN')
        self.send_command('AT+CLCK="SC",0,"{}"'.format(current_pin))
        self.get_response()


def debug(message):
    print('DEBUG:', message)


def error(message):
    print('ERROR:', message)


def info(message, verbose=True):
    if verbose:
        print('INFO:', message)


def warning(message):
    print('WARNING:', message)


def getch():
    """Helper for prompt_for_pin()."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def prompt_for_pin(message, length=4):
    """Ask the user for a PIN."""
    key = ""
    sys.stdout.write(message + ': ')
    while True:
        ch = getch()
        if ch == '\r':
            break
        key += ch
        sys.stdout.write('*')
    print()
    if not key.isdigit():
        prompt_yes_or_exit('Your PIN contains non-digits. Continue?')
    if len(key) < length:
        prompt_yes_or_exit(
            'Your PIN is shorter than {} digits. Continue?'.format(length))
    if len(key) > length:
        prompt_yes_or_exit(
            'Your PIN is longer than {} digits. Continue?'.format(length))
    return key


def prompt_yes_or_exit(message):
    """Ask the user for yes or no."""
    reply = str(raw_input(message + ' (y/N): ')).lower().strip()
    if reply == 'y' or reply == 'yes':
        return True
    sys.exit(1)


def parse_arguments():
    """Get commandline arguments."""
    parser = argparse.ArgumentParser(
        description='Change PIN of a SIM card via UMTS/LTE modem')
    parser.add_argument('--modem', '-m', default='/dev/ttyUSB2',
                        help='Location of UMTS/LTE device file')
    parser.add_argument('--modem-info', action='store_true',
                        help='Print modem info and exit')
    parser.add_argument('--disable', '-d', action='store_true',
                        help='Disable PIN instead of changing it')
    parser.add_argument('--reset', action='store_true',
                        help='Reset the modem')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debugging')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show additional information')
    return parser.parse_args()


def main():
    args = parse_arguments()
    try:
        verbose = (args.verbose or args.debug)
        modem = Modem(args.modem, args.debug, verbose)
        if args.modem_info:
            modem.verbose = True
            modem.print_modem_info()
            return

        if args.reset:
            modem.reset()
            return

        # unlock sim (if needed)
        if modem.sim_is_locked():
            modem.unlock_sim()
            if modem.sim_is_locked():
                raise ModemException('Could not unlock SIM card (wrong PIN?).')

        if modem.sim_is_pin_protected():
            if (args.disable):
                modem.disable_pin()
                info('The PIN has been successfully disabled.')
            else:
                modem.change_pin()
                info('The PIN has been successfully changed.')
        else:
            # ask for new PIN unless --disable is requested
            if (args.disable):
                info('The PIN has already been disabled.')
            else:
                # Set a PIN for PIN-less SIM card
                modem.change_pin(enabled=False)

    except serial.serialutil.SerialException, e:
        error('Could not initialize modem: {}'.format(e))
    except (UnexpectedResponseException, ModemException), e:
        error('{}: {}'.format(e.__class__.__name__, e))


if __name__ == '__main__':
    main()
