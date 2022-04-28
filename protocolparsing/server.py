"""Implementation of the TCP server"""
import base64
import logging
import random
import socket
import threading
import time
from dataclasses import dataclass

import config
from utils import WireProtocol


def generate_random_data(
        min_temperature=config.MIN_TEMPERATURE_INT,
        max_temperature=config.MAX_TEMPREATURE_INT,
        min_humidity=config.MIN_HUMIDITY_INT,
        max_humidity=config.MAX_HUMIDITY_INT) -> tuple[int, int]:
    temperature = random.randrange(min_temperature, max_temperature)
    humidity = random.randrange(min_humidity, max_humidity)
    return temperature, humidity


@dataclass
class Server:
    """TCP server responsible for serving sensor data"""
    host_ip: str = config.SERVER_IP_ADDRESS
    port: int = config.SERVER_PORT
    wp: WireProtocol = WireProtocol()

    def __post_init__(self):
        self.server_socket = socket.create_server((self.host_ip, self.port))

    def make_header(self, packed_data: bytes) -> bytes:
        """Create package header specifying the packe size"""
        return f"{len(packed_data):<{config.HEADER_SIZE}}".encode()

    def fetch_package(self) -> bytes:
        """Make new package prepended with a size header"""
        data = generate_random_data()
        packed_data = base64.b64encode(self.wp.pack(data))
        return self.make_header(packed_data) + packed_data

    def on_client_connect(self, client_socket: socket.SocketType,
                          main_thread_finished: threading.Event):
        """Callback function executed by a worker thread on new client connection"""
        try:
            while True:
                if main_thread_finished.is_set():
                    break

                client_socket.sendall(self.fetch_package())
                time.sleep(3)
        except Exception as e:
            logging.error(
                f"Worker thread exception, {e}, while sending to {client_socket}"
            )
        finally:
            client_socket.close()

    def listen(self):
        """Starts server process event loop listening for client connections"""
        threads = []
        main_thread_finished = threading.Event()
        try:
            while True:
                client_socket, _ = self.server_socket.accept()
                thread = threading.Thread(target=self.on_client_connect,
                                          args=(client_socket,
                                                main_thread_finished))
                threads.append(thread)
                thread.start()
        except Exception as e:
            logging.critical(f"Server exception, {e}")
        finally:
            main_thread_finished.set()
            for thread in threads:
                thread.join()


if __name__ == "__main__":
    try:
        server = Server()
        server.listen()
    except OSError as e:
        logging.critical(f"Server exception, {e}")
