import pytest

from protocolparsing import utils


class TestWireProtocol:

    def test_tuple_of_ints(self):
        data = (1234, 5678)
        wp = utils.WireProtocol()
        packed_data = wp.pack(data)
        assert wp.unpack(packed_data) == data

    def test_pack_input_does_not_match_format(self):
        data = (12.34, 56.78)
        wp = utils.WireProtocol()
        with pytest.raises(utils.WireProtocolError):
            wp.pack(data)

    def test_unpack_input_does_not_match_format(self):
        data = (12.34, 56.78)
        package_info = utils.Package(data_format="!ff")
        packed_data = utils.WireProtocol(package_info).pack(data)
        wp = utils.WireProtocol()
        assert wp.unpack(packed_data) != data

    def test_covert_to_nominal_units(self):
        data = (1234, 5678)
        result = (12.34, 56.78)
        wp = utils.WireProtocol()
        assert wp.to_nominal_units(data) == pytest.approx(result)


def test_process_package_success():
    package = b"NAkAALoLAAA="
    result = (23.56, 30.02)
    package_info = utils.Package(data_format="<ii")
    wp = utils.WireProtocol(package_info)
    assert utils.process_package(package, wp) == result


def test_process_package_failure():
    package = b"helloworld"
    wp = utils.WireProtocol()
    assert utils.process_package(package, wp) is None
