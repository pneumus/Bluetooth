import sys
import time
from PySide6.QtCore import QCoreApplication, QTimer, QObject, Slot, QEventLoop
from PySide6.QtBluetooth import QBluetoothDeviceDiscoveryAgent, QLowEnergyController, QBluetoothDeviceInfo


class BLEManager(QObject):
    def __init__(self):
        super().__init__()
        self.app = QCoreApplication.instance()
        if not self.app:
            self.app = QCoreApplication(sys.argv)

        self.discovery_agent = QBluetoothDeviceDiscoveryAgent(self)
        self.devices = []
        self._device_cache = {}
        self.controller = None
        self._is_connected = False

        self.discovery_agent.deviceDiscovered.connect(self._add_device)

    @Slot(object)
    def _add_device(self, device):
        if device not in self.devices:
            self.devices.append(device)
            self._device_cache[device.address().toString()] = device

    def scan_ble_devices(self, timeout_ms=5000):
        """Scans for BLE devices and returns a list of dictionaries."""
        self.devices = []
        self._device_cache = {}
        local_loop = QEventLoop()

        self.discovery_agent.finished.connect(local_loop.quit)

        def handle_timeout():
            self.discovery_agent.stop()
            local_loop.quit()

        self.discovery_agent.start(QBluetoothDeviceDiscoveryAgent.DiscoveryMethod.LowEnergyMethod)

        timeout_timer = QTimer(self)
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(handle_timeout)
        timeout_timer.start(timeout_ms)

        local_loop.exec()
        timeout_timer.stop()

        try:
            self.discovery_agent.finished.disconnect(local_loop.quit)
        except (RuntimeWarning, RuntimeError):
            pass

        return [
            {"name": device.name(), "address": device.address().toString()}
            for device in self.devices if device.name()
        ]

    def connect_to_mac(self, mac_address: str, timeout_ms=10000) -> bool:
        """
        Attempts to connect to a BLE device. Blocks until connected
        or timed out, then leaves the connection channel active.
        """
        if self._is_connected:
            print("Already connected to a device.")
            return True

        target_mac = mac_address.upper()
        device_info = self._device_cache.get(target_mac)

        if not device_info:
            print(f"Error: Target device {target_mac} was not found in scan cache.")
            return False

        print(f"Connecting to {target_mac}...")

        self.controller = QLowEnergyController.createCentral(device_info, self)
        self._is_connected = False

        local_loop = QEventLoop()

        @Slot()
        def on_connected():
            self._is_connected = True
            print("Successfully connected! Discovering services...")
            self.controller.discoverServices()
            local_loop.quit()

        @Slot(QLowEnergyController.Error)
        def on_error(error):
            print(f"Connection error occurred: {error}")
            self._is_connected = False
            local_loop.quit()

        def on_timeout():
            print("Connection attempt timed out.")
            if self.controller:
                self.controller.disconnectFromDevice()
            local_loop.quit()

        # Wire up live connection monitors
        self.controller.connected.connect(on_connected)
        self.controller.errorOccurred.connect(on_error)

        timeout_timer = QTimer(self)
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(on_timeout)
        timeout_timer.start(timeout_ms)

        self.controller.connectToDevice()
        local_loop.exec()
        timeout_timer.stop()

        if not self._is_connected and self.controller:
            self.controller.deleteLater()
            self.controller = None

        return self._is_connected

    def disconnect(self):
        """Manually disconnects from the BLE device and blocks cleanly until fully closed."""
        if not self.controller:
            print("No active controller connection found.")
            return

        print("Disconnecting from device...")
        self._is_connected = False

        # Check if it's already disconnected to skip unnecessary waiting
        if self.controller.state() == QLowEnergyController.ControllerState.UnconnectedState:
            self.controller.deleteLater()
            self.controller = None
            print("Disconnected successfully (already closed).")
            return

        # Create a local block loop to wait specifically for the disconnection to finish
        disconnect_loop = QEventLoop()
        self.controller.disconnected.connect(disconnect_loop.quit)

        # Trigger the asynchronous disconnect pipeline
        self.controller.disconnectFromDevice()

        # Block the script right here until the hardware confirms it is fully disconnected
        disconnect_loop.exec()

        # Clean cleanup now that we are guaranteed to be in UnconnectedState
        self.controller.deleteLater()
        self.controller = None
        print("Disconnected successfully and cleaned up.")


if __name__ == "__main__":

    TARGET_MAC = "CE:EE:A8:9B:17:AC"
    ble_manager = BLEManager()
    ble_devices = ble_manager.scan_ble_devices(timeout_ms=3000)

    device_found = any(device["address"] == TARGET_MAC for device in ble_devices)
    if device_found:
        # Use the target MAC explicitly here to avoid signature errors
        success = ble_manager.connect_to_mac(TARGET_MAC, timeout_ms=5000)

    time.sleep(1)
    ble_manager.disconnect()
