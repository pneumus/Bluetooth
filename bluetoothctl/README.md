### Hands-on Libraries for Bluetooth

<b>Note:</b> some of the methods in this library need elevated privileges
<br>
i.e. set_adapter_state() or set_service_state()
<br>

#### Discovery Sample Code for btct_wrapper.py

```python
from bluetoothctl.btct_wrapper import BluetoothControl as BtCt

comm = BtCt()
for device in comm.discover_devices():
    print(device)
```


#### Connection Sample Code for btct_wrapper.py

```python
from bluetoothctl.btct_wrapper import BluetoothControl as BtCt

comm = BtCt()
mac_address = "6E:FF:A8:93:CC:65"

comm.discover_devices()
comm.connect(mac_address)
print(comm.is_connected)
comm.disconnect()
```


#### Communication Sample Code for btct_wrapper.py

```python
from bluetoothctl.btct_wrapper import BluetoothControl as BtCt

comm = BtCt()
mac_address = "6E:FF:A8:93:CC:65"

comm.discover_devices()
comm.connect(mac_address)
response = comm.communicate("AT\r\n")
print(response)
```
