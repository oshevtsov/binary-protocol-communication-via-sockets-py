"""Implementation of the TCP client"""
import logging
import socket
from dataclasses import dataclass

import config
from utils import DataType
from utils import process_package
from utils import WireProtocol


@dataclass
class Client:
    """TCP client receiving sensor data from a server"""
    server_ip: str = config.SERVER_IP_ADDRESS
    server_port: int = config.SERVER_PORT
    wp: WireProtocol = WireProtocol()

    def __post_init__(self):
        self.client_socket = socket.create_connection(
            (self.server_ip, self.server_port),
            timeout=config.CLIENT_CONNECTION_TIMEOUT)

    def __del__(self):
        self.client_socket.close()

    def receive_package(self) -> bytes:
        """Receives and returns a new package from the server"""
        package = b""
        is_first_chunk = True
        package_size = -1
        while True:
            data = self.client_socket.recv(config.PACKAGE_CHUNK_SIZE)
            if not data:
                return package

            if is_first_chunk:
                package_size = int(data[:config.HEADER_SIZE].decode())
                is_first_chunk = False
            package += data

            if len(package) - config.HEADER_SIZE == package_size:
                break
        return package[config.HEADER_SIZE:]

    def display_package_data(self, package_data: DataType):
        """Displays received package data"""
        display_message_bits = []
        for tag, value in zip(self.wp.package_info.data_fields, package_data):
            display_message_bits.append(f"{tag} = {value:.2f}")
        print(", ".join(display_message_bits))

    def connect(self):
        """Starts the client process event loop waiting for incoming packages"""
        while True:
            package = self.receive_package()
            if not package:
                logging.warning("Server disconnected. Shutting down...")
                break

            package_data = process_package(package, self.wp)
            if package_data and self.wp.validate_data_type(package_data):
                self.display_package_data(package_data)
            else:
                logging.warning(f"Received corrupted package, {package_data}")


if __name__ == "__main__":
    try:
        client = Client()
        client.connect()
    except OSError as e:
        logging.critical(f"Client exception, {e}")
