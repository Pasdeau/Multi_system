import asyncio
import csv
import sys
import time
from itertools import count, takewhile
from typing import Iterator

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


# Helper function to split data into chunks
def sliced(data: bytes, n: int) -> Iterator[bytes]:
    """
    Slices *data* into chunks of size *n*. The last slice may be smaller than
    *n*.
    """
    return takewhile(len, (data[i: i + n] for i in count(0, n)))


async def uart_terminal():
    """
    A simple program that uses the Nordic Semiconductor (nRF) UART service.
    It receives 12 bytes of data and logs the values of LED1, LED2, LED3, and LED4.
    """

    # Initialize CSV file
    with open("led_data.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "670nm", "850nm", "950nm", "1300nm"])  # CSV header
        file.flush()

    def match_nus_uuid(device: BLEDevice, adv: AdvertisementData):
        # Filter for devices with the specified UART service UUID
        if UART_SERVICE_UUID.lower() in adv.service_uuids:
            return True
        return False

    device = await BleakScanner.find_device_by_filter(match_nus_uuid)

    if device is None:
        print("No matching device found. You may need to edit match_nus_uuid().")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected. Goodbye.")
        for task in asyncio.all_tasks():
            task.cancel()
        file.close()

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        # Extract LED values from the received data
        a = int((data[0:3].hex()), 16)
        b = int((data[3:6].hex()), 16)
        c = int((data[6:9].hex()), 16)
        d = int((data[9:12].hex()), 16)

        # Convert to float values
        led1 = int(a) / 8388608.0 * 4.0
        led2 = int(b) / 8388608.0 * 4.0
        led3 = int(c) / 8388608.0 * 4.0
        led4 = int(d) / 8388608.0 * 4.0

        # Get the current timestamp
        timestamp = time.time()

        # Log the data to the CSV file
        with open("led_data.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, led1, led2, led3, led4])
            file.flush()

        # Print received data (optional, for debugging)
        print(f"Time: {timestamp}, 670nm: {led1}, 850nm: {led2}, 950nm: {led3}, 1300nm: {led4}")

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        print("Connected. Start typing and press ENTER to send data...")

        loop = asyncio.get_running_loop()
        nus = client.services.get_service(UART_SERVICE_UUID)
        rx_char = nus.get_characteristic(UART_RX_CHAR_UUID)

        while True:
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)
            if not data:
                break
            for s in sliced(data, rx_char.max_write_without_response_size):
                await client.write_gatt_char(rx_char, s)
            print("Sent:", data)


if __name__ == "__main__":
    try:
        asyncio.run(uart_terminal())
    except asyncio.CancelledError:
        pass
