import asyncio
import time
from unittest import mock

import pytest
import json

from mcstatus.address import Address
from mcstatus.pinger import AsyncServerPinger
from mcstatus.protocol.connection import Connection


def async_decorator(f):
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


class FakeAsyncConnection(Connection):
    async def read_buffer(self):
        return super().read_buffer()


class TestAsyncServerPinger:
    @classmethod
    @pytest.fixture(autouse=True)
    def setup(cls, faker):
        cls.pinger = AsyncServerPinger(
            FakeAsyncConnection(),  # type: ignore[arg-type]
            address=Address(faker.domain_name(3), faker.pyint(1, 65535)),
            version=faker.pyint(),
        )

    def test_handshake(self):
        self.pinger.handshake()

        assert self.pinger.connection.flush() == bytearray(b'"\x00\x98G\x1b' + self.pinger.address.host.encode("utf-8") + b'\x01\xb5\x01')

    def test_read_status(self, faker):
        expected = {
            "description": faker.sentence(),
            "players": {"max": faker.pyint(), "online": faker.pyint()},
            "version": {"name": faker.pystr(), "protocol": faker.pyint()},
        }
        input = bytearray(b"r\x00p")
        input.extend(json.dumps(expected).encode("utf-8"))
        self.pinger.connection.receive(input)
        status = async_decorator(self.pinger.read_status)()

        assert status.raw == expected
        assert self.pinger.connection.flush() == bytearray.fromhex("0100")

    def test_read_status_invalid_json(self):
        self.pinger.connection.receive(bytearray(b"\x03\x00\x01{"))
        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_read_status_invalid_reply(self, faker):
        expected = {
            "players": {"max": faker.pyint(), "online": faker.pyint()},
            "version": {"name": faker.pystr(), "protocol": faker.pyint()},
        }
        input = bytearray(b"r\x00p")
        input.extend(json.dumps(expected).encode("ascii"))
        self.pinger.connection.receive(input)

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_read_status_invalid_status(self):
        self.pinger.connection.receive(bytearray.fromhex("0105"))

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_test_ping(self):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = 14515484

        assert async_decorator(self.pinger.test_ping)() >= 0
        assert self.pinger.connection.flush() == bytearray.fromhex("09010000000000DD7D1C")

    def test_test_ping_invalid(self, faker):
        self.pinger.connection.receive(bytearray.fromhex("011F"))
        self.pinger.ping_token = faker.pyint()

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    def test_test_ping_wrong_token(self, faker):
        self.pinger.connection.receive(bytearray.fromhex("09010000000000DD7D1C"))
        self.pinger.ping_token = faker.pyint()

        with pytest.raises(IOError):
            async_decorator(self.pinger.test_ping)()

    @pytest.mark.asyncio
    async def test_latency_is_real_number(self, faker):
        """`time.perf_counter` returns fractional seconds, we must convert it to milliseconds."""
        expected = {
            "description": faker.sentence(),
            "players": {"max": faker.pyint(), "online": faker.pyint()},
            "version": {"name": faker.pystr(), "protocol": faker.pyint()},
        }
        input = bytearray(b"r\x00p")
        input.extend(json.dumps(expected).encode("ascii"))

        def mocked_read_buffer():
            time.sleep(0.001)
            return mock.DEFAULT

        with mock.patch.object(FakeAsyncConnection, "read_buffer") as mocked:
            mocked.side_effect = mocked_read_buffer
            mocked.return_value.read_varint = lambda: 0  # overwrite `async` here
            mocked.return_value.read_utf = lambda: json.dumps(expected)  # overwrite `async` here
            pinger = AsyncServerPinger(
                FakeAsyncConnection(),  # type: ignore[arg-type]
                address=Address(faker.domain_name(3), faker.pyint(1, 65535)),
                version=faker.pyint(),
            )

            pinger.connection.receive(input)
            # we slept 1ms, so this should be always ~1.
            assert (await pinger.read_status()).latency >= 1

    @pytest.mark.asyncio
    async def test_test_ping_is_in_milliseconds(self, faker):
        """`time.perf_counter` returns fractional seconds, we must convert it to milliseconds."""

        def mocked_read_buffer():
            time.sleep(0.001)
            return mock.DEFAULT

        with mock.patch.object(FakeAsyncConnection, "read_buffer") as mocked:
            mocked.side_effect = mocked_read_buffer
            mocked.return_value.read_varint = lambda: 1  # overwrite `async` here
            mocked.return_value.read_long = faker.pyint  # overwrite `async` here
            pinger = AsyncServerPinger(
                FakeAsyncConnection(),  # type: ignore[arg-type]
                address=Address(faker.domain_name(3), faker.pyint(1, 65535)),
                version=faker.pyint(),
                ping_token=faker.pyint(),
            )
            # we slept 1ms, so this should be always ~1.
            assert await pinger.test_ping() >= 1
