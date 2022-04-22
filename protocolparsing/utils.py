"""Functions and classes shared between clients and servers"""
import base64
import binascii
import logging
import struct
from dataclasses import dataclass
from typing import Callable
from typing import get_args
from typing import get_origin
from typing import NamedTuple
from typing import Optional
from typing import Type

NUMERIC_TYPE = float
DEFAULT_PACKAGE_DATA_TYPE = tuple[NUMERIC_TYPE, NUMERIC_TYPE]
DEFAULT_PACKAGE_FORMAT = "!ii"
DEFAULT_DATA_FIELDS = ["Temperature", "Humidity"]

DataType = tuple[NUMERIC_TYPE, ...]
WireProtocolError = struct.error
ConvertStrategy = Callable[[NUMERIC_TYPE], NUMERIC_TYPE]


class Package(NamedTuple):
    """Struct containing wire protocol configuration"""
    data_format: str = DEFAULT_PACKAGE_FORMAT
    data_type: Type = DEFAULT_PACKAGE_DATA_TYPE
    data_fields: list[str] = DEFAULT_DATA_FIELDS


def double_digit_converter(value: NUMERIC_TYPE) -> NUMERIC_TYPE:
    """Converts parsed wire protocol value to nominal units"""
    return round(value * 10**-2, 2)


@dataclass
class WireProtocol:
    """Class implementing the wire protocol functionality"""
    package_info: Package = Package()
    converter: ConvertStrategy = double_digit_converter

    def pack(self, values: DataType) -> bytes:
        """Pack a tuple of values to a bytes array"""
        return struct.pack(self.package_info.data_format, *values)

    def unpack(self, packed_data: bytes) -> DataType:
        """Unpack the bytes array onto a tuple of values"""
        return struct.unpack(self.package_info.data_format, packed_data)

    def to_nominal_units(self, values: DataType) -> DataType:
        """Converts parsed wire protocol data to nominal units"""
        return tuple(map(self.converter, values))

    def extract_package_data(self, packed_data: bytes) -> DataType:
        """Extract a tuple of values in nominal units from a bytes array"""
        extracted_data = self.to_nominal_units(self.unpack(packed_data))

        if not self.validate_data_type(extracted_data):
            message = f"Unpacked data is of incompatible data type, {type(extracted_data)}"
            logging.error(message)
            raise WireProtocolError(message)
        return extracted_data

    def validate_data_type(self, data: DataType) -> bool:
        """Validate that the data agrees with the protocol configuration"""
        if not type(data) is get_origin(self.package_info.data_type):
            return False
        matches_size = len(data) == len(get_args(self.package_info.data_type))
        matches_type = all(map(lambda e: isinstance(e, NUMERIC_TYPE), data))
        return matches_size and matches_type


def do_process_package(package: bytes,
                       wire_protocol: WireProtocol) -> DataType:
    package_bytes = base64.b64decode(package, validate=True)
    return wire_protocol.extract_package_data(package_bytes)


def process_package(package: bytes,
                    wire_protocol: WireProtocol) -> Optional[DataType]:
    """Process the incoming base-64 package to a tuple of values

    This is a higher-level method that leverages the wire protocol to parse
    packages. If processing fails, the function returns `None`.

    Arguments:
        package -- base-64 encoded package received from the server
        wire_protocol -- instance of WireProtocol class
    """
    try:
        return do_process_package(package, wire_protocol)
    except (binascii.Error, WireProtocolError):
        logging.error(f"Could not process the package, {package}")
        return None
