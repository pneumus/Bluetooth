from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtBluetooth import QBluetoothDeviceDiscoveryAgent

class BLEScanner:
    def __init__(self):
        self.app = QCoreApplication([])  # Create a Qt application instance
        self.discovery_agent = QBluetoothDeviceDiscoveryAgent()
        self.devices = []

        # Connect signals
        self.discovery_agent.deviceDiscovered.connect(self._add_device)
        self.discovery_agent.finished.connect(self._stop_discovery)

    def _add_device(self, device):
        # Add device to the list if it's not already there
        if device not in self.devices:
            self.devices.append(device)

    def _stop_discovery(self):
        self.discovery_agent.stop()

    def scan_ble_devices(self):
        # Start the device discovery process
        self.devices = []
        self.discovery_agent.start()

        # Run the event loop for a short period to allow device discovery
        QTimer.singleShot(5000, self.app.quit)  # Adjust the timeout as needed
        self.app.exec()

        # Return a list of discovered devices (as QBluetoothDeviceInfo objects)
        return [device.name() for device in self.devices]

# Usage Example
if __name__ == "__main__":
    scanner = BLEScanner()
    ble_devices = scanner.scan_ble_devices()
    print("Discovered BLE devices:", ble_devices)
