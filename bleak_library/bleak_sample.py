import asyncio
from bleak import BleakScanner


class BLEScanner:
    async def scan_nearby_devices(self, scan_duration=3):
        """
        Scans for nearby BLE devices and returns a list of discovered devices.

        :param scan_duration: Duration to scan for devices in seconds.
        :return: A list of tuples containing the device address and name.
        """
        devices = await BleakScanner.discover(timeout=scan_duration)
        return [(device.address, device.name) for device in devices]


scanner = BLEScanner()
nearby_devices = asyncio.run(scanner.scan_nearby_devices())

for address, name in nearby_devices:
    print(f"Device Address: {address}, Device Name: {name}")