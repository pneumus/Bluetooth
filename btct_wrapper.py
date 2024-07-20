# A simple Python Wrapper for bluetoothctl ( Linux )
# Author: Máté Gál
# Contact: gal.mateo@gmail.com

# Note: 
# One known issue is that discovery is flooding the terminal 
# and blocking / slowing other commands
# A non-interactive call could solve this
# i.e. "sudo bluetoothctl --timeout 3 mgmt.find"
# but this command does not register the MAC address 
# so connection is not working at the moment

import re
import ptyprocess
import subprocess
import logging
logging.basicConfig(level=logging.DEBUG)


class BluetoothControl:

    @staticmethod
    def check_service_and_adapter_running():
        if not BluetoothControl.get_service_state(logger=False):
            raise RuntimeError('Bluetooth Service is not running')
        if not BluetoothControl.get_adapter_state(logger=False):
            raise RuntimeError('Bluetooth Adapter is not turned on')

    @staticmethod
    def check_connection_state():
        if not BluetoothControl.is_connected():
            raise RuntimeError('Bluetooth Device is not connected')

    @staticmethod
    def get_service_state(logger=True):
        try:
            command = ['sudo', 'systemctl', 'is-active', '--quiet', 'bluetooth']
            process = subprocess.Popen(command, shell=False)
            while True:
                return_code = process.poll()
                if return_code == 3:
                    state = False
                    break
                elif return_code == 0:
                    state = True
                    break
            if logger:
                logging.debug("Service state: " + str(state))
            return state
        except Exception as e:
            logging.error(f'Unable to get Bluetooth Service State\nException : {e}')

    @staticmethod
    def set_service_state(state, logger=True):
        try:
            if logger:
                logging.debug(f"Setting service State to {state}")
            if state:
                command = ['sudo', 'systemctl', 'enable', '--now', '--quiet', 'bluetooth']
            else:
                command = ['sudo', 'disable', '--now', '--quiet', 'bluetooth']
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, shell=False)
            # Wait for the process to finish
            while True:
                return_code = process.poll()
                if return_code is None:
                    pass
                elif return_code == 0:
                    return True
                else:
                    raise Exception('Return code of process not zero')
        except Exception as e:
            logging.error(f'Unable to set Bluetooth Service State\nException : {e}')

    @staticmethod
    def get_adapter_state(logger=True):
        try:
            if BluetoothControl.get_service_state(logger=False):
                state = False
                command = ['sudo', 'bluetoothctl', 'show']
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                output = result.stdout
                lines = output.split('\n')
                for line in lines:
                    if "Powered" in line:
                        if "yes" in line:
                            state = True
                if logger:
                    logging.debug("Adapter State: " + str(state))
                return state
            else:
                raise RuntimeError('Bluetooth Service is not running')
        except Exception as e:
            logging.error(f'Unable to get Bluetooth Adapter State\nException : {e}')

    @staticmethod
    def set_adapter_state(state, logger=True):
        try:
            if logger:
                logging.debug("Setting adapter State to " + str(state))
            if BluetoothControl.get_service_state(logger=False):
                if state:
                    command = ['sudo', 'bluetoothctl', 'power', 'on']
                else:
                    command = ['sudo', 'bluetoothctl', 'power', 'off']
                process = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL, shell=False)
                # Wait for the process to finish
                while True:
                    return_code = process.poll()
                    if return_code is None:
                        pass
                    elif return_code == 0:
                        return True
                    else:
                        raise Exception('Return code of process not zero')
            else:
                raise RuntimeError('Bluetooth Service is not running')
        except Exception as e:
            logging.error(f'Unable to set Bluetooth Adapter State\nException : {e}')

    @staticmethod
    def discover_devices(timeout=3, logger=True):
        """
        The method returns the MAC addresses of nearby devices
        Input arguments are timeout in seconds and a boolean value to turn on logging
        Note: Instead of "bluetoothctl --timeout 3 scan on" another apporach "mgmt.find" is used
        otherwise the interactive shell is flooded with newly found devices
        """
        try:
            command = ['sudo', 'bluetoothctl', '--timeout', f'{timeout}', 'scan', 'on']
            process = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
            # Read and process the output
            mac_addresses = []
            for line in process.stdout:
                line = line.strip()
                if "Device" in line:
                    mac_address = line.split(" ")[2]
                    mac_addresses.append(mac_address)
                    if logger:
                        logging.debug(f'Device found! MAC: {mac_address}')
            # Wait for the process to finish
            while True:
                return_code = process.poll()
                if return_code == 0:
                    break
            if len(mac_addresses) == 0:
                if logger:
                    logging.debug("No nearby Bluetooth devices found.\n")
                return False
            return mac_addresses
        except Exception as e:
            logging.error(f'Unable to discover nearby Bluetooth Devices\nException : {e}')

    @staticmethod
    def connect(mac_address):
        BluetoothControl.check_service_and_adapter_running()
        try:
            logging.debug(f"Connecting to {mac_address}")
            command = ['sudo', 'bluetoothctl', 'connect', str(mac_address)]
            response = subprocess.run(command, timeout=3, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL, shell=False)
            if response.returncode == 0:
                return True
            else:
                raise Exception(f'Return code of process not zero. Return code: {response.returncode}')
        except Exception as e:
            logging.error(f'Unable to connect to the following device: {mac_address}\nException : {e}')

    @staticmethod
    def disconnect():
        BluetoothControl.check_connection_state()
        BluetoothControl.check_service_and_adapter_running()
        try:
            logging.debug("Disconnecting from device ...")
            command = ['sudo', 'bluetoothctl', 'disconnect']
            response = subprocess.run(command, stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL, shell=False)
            if response.returncode == 0:
                return True
            else:
                return False
        except Exception as e:
            logging.error(f'Unable to disconnect from Bluetooth Device\nException : {e}')

    @staticmethod
    def is_connected():
        BluetoothControl.check_service_and_adapter_running()
        try:
            commands = ['sudo', 'bash', '-c', 'echo -e info | bluetoothctl | grep Connected']
            process = subprocess.run(commands, capture_output=True, text=True, check=True)
            if 'Connected: yes' in process.stdout:
                return True
            return False
        except Exception as e:
            logging.error(f'Unable to check Bluetooth Connection State\nException : {e}')

    @staticmethod
    def list_gatt_uuids():
        BluetoothControl.check_service_and_adapter_running()
        BluetoothControl.check_connection_state()
        try:
            command = ['sudo', 'bluetoothctl', 'gatt.list-attributes']
            output = subprocess.check_output(command).decode().split()
            # Regular expression to filter specific UUID format
            uuids = []
            pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
            for line in output:
                if pattern.match(line.strip()):
                    uuids.append(line.strip())
            return uuids
        except Exception as e:
            logging.error(f'Unable to list GATT UUIDs\nException : {e}')

    @staticmethod
    def communicate(write_uuid, read_uuid, data):
        try:
            """
            Requires a writable and/or a readable GATT uuid and data to be written
            The method returns the data retrieved from the readable GATT uuid
            """

            BluetoothControl.check_service_and_adapter_running()
            BluetoothControl.check_connection_state()

            # Converting data to HEX values
            hex_string = ''
            for char in data:
                hex_string += hex(ord(char)) + ' '

            # # Starting a pseudo terminal to read
            read_process = ptyprocess.PtyProcessUnicode.spawn(['sudo', '/bin/bash'])
            read_process.setwinsize(100, 100)
            commands = ['bluetoothctl', 'menu gatt', f'select-attribute {read_uuid}', 'notify on']
            for command in commands:
                for char in command:
                    read_process.write(char)
                read_process.write('\n')
                read_process.flush()

            # Starting a pseudo terminal to write
            write_process = ptyprocess.PtyProcessUnicode.spawn(['sudo', '/bin/bash'])
            commands = f'bluetoothctl <<EOF\nmenu gatt\nselect-attribute {write_uuid}\nwrite "{hex_string}"\nEOF\n'
            write_process.write(commands)
            write_process.flush()

            # Read until new line ( hex: 0a )
            lines = ''
            for char in range(5000):
                lines += read_process.read(1)
                if lines[char] == 'a':
                    if lines[char - 1] == '0':
                        if lines[char - 2] == ' ':
                            break
                if lines[char] == '':
                    break
            lines = lines.splitlines()

            # Get the important part of the response
            response = []
            append = False
            for line_num, line in enumerate(lines):
                if "Value" in line:
                    append = True
                if append:
                    response.append(line)

            # Filter the HEX values
            hex_values = []
            matches = []
            for line in response:
                pattern1 = r'  (.*?)  '
                matches.extend(re.findall(pattern1, line))
                pattern2 = r'  .*?0a'
                matches.extend(re.findall(pattern2, line))
            for match in matches:
                for number in str(match).split():
                    hex_values.append(number)

            # Convert HEX values to an ASCII string
            ascii_string = ''.join(chr(int(hex_val, 16)) for hex_val in hex_values)

            logging.debug(f"Writing GATT Characteristic:\n\t"
                          f"Write UUID: {write_uuid}\n\t"
                          f"Read UUID: {read_uuid}\n\t"
                          f"Data: {repr(data)}\n\t"
                          f"HEX: {hex_string}\n\t"
                          f"Response: {ascii_string}")

            return ascii_string
        except Exception as e:
            logging.error(f'Unable to communicate with Bluetooth Device\nException : {e}')
