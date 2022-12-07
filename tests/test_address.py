from __future__ import annotations

import ipaddress
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import dns.resolver
import pytest
from dns.rdatatype import RdataType

from mcstatus.address import Address, async_minecraft_srv_address_lookup, minecraft_srv_address_lookup
from tests.factories import AddressFactory, StringAddressFactory, StubAddressFactory


class TestSRVLookup:
    @pytest.mark.parametrize("exception", [dns.resolver.NXDOMAIN, dns.resolver.NoAnswer])
    def test_address_no_srv(self, exception, faker):
        host, port = StubAddressFactory()
        with patch("dns.resolver.resolve") as resolve:
            resolve.side_effect = [exception]
            address = minecraft_srv_address_lookup(host, default_port=port, lifetime=3)
            resolve.assert_called_once_with(f"_minecraft._tcp.{host}", RdataType.SRV, lifetime=3)

        assert address.host == host
        assert address.port == port

    def test_address_with_srv(self, faker):
        host, port = StubAddressFactory()
        with patch("dns.resolver.resolve") as resolve:
            answer = Mock()
            answer.target = host
            answer.port = port
            resolve.return_value = [answer]

            address = minecraft_srv_address_lookup(host, lifetime=3)
            resolve.assert_called_once_with(f"_minecraft._tcp.{host}", RdataType.SRV, lifetime=3)
        assert address.host == host
        assert address.port == port

    @pytest.mark.asyncio
    @pytest.mark.parametrize("exception", [dns.resolver.NXDOMAIN, dns.resolver.NoAnswer])
    async def test_async_address_no_srv(self, exception, faker):
        domain, port = StubAddressFactory()
        with patch("dns.asyncresolver.resolve") as resolve:
            resolve.side_effect = [exception]
            address = await async_minecraft_srv_address_lookup(domain, default_port=port, lifetime=3)
            resolve.assert_called_once_with(f"_minecraft._tcp.{domain}", RdataType.SRV, lifetime=3)

        assert address.host == domain
        assert address.port == port

    @pytest.mark.asyncio
    async def test_async_address_with_srv(self, faker):
        domain, port = StubAddressFactory()
        with patch("dns.asyncresolver.resolve") as resolve:
            answer = Mock()
            answer.target = domain + "."
            answer.port = port
            resolve.return_value = [answer]

            address = await async_minecraft_srv_address_lookup(domain, lifetime=3)
            resolve.assert_called_once_with(f"_minecraft._tcp.{domain}", RdataType.SRV, lifetime=3)
        assert address.host == domain
        assert address.port == port


class TestAddressValidity:
    @pytest.mark.parametrize(
        "method",
        [
            "domain_name",
            "ipv4",
            "ipv6",
        ],
    )
    def test_address_validation_valid(self, method, faker):
        address, port = getattr(faker, method)(), StubAddressFactory().port
        Address._ensure_validity(address, port)

    @pytest.mark.parametrize(
        "input,exception",
        [
            # Out of range port
            ("faker.domain_name(3), faker.pyint(65535, 100_000)", ValueError),
            ("faker.domain_name(3), -1", ValueError),
            # Invalid types
            ("faker.domain_name(3), str(faker.port_number())", TypeError),
            ("faker.port_number(), faker.domain_name(3)", TypeError),
            ("(faker.domain_name(3), faker.port_number()), None", TypeError),
            ("0, 0", TypeError),
            ("'', ''", TypeError),
        ],
    )
    def test_address_validation_invalid(self, input, exception, faker):
        with pytest.raises(exception):
            Address._ensure_validity(*eval(input, {"faker": faker}))


class TestAddressConstructing:
    def test_init_constructor(self, faker):
        domain, port = StubAddressFactory()
        addr = Address(domain, port)
        assert addr.host == domain
        assert addr.port == port

    def test_tuple_behavior(self, faker):
        domain, port = StubAddressFactory()
        addr = Address(domain, port)
        assert isinstance(addr, tuple)
        assert len(addr) == 2
        assert addr[0] == domain
        assert addr[1] == port

    def test_from_tuple_constructor(self, faker):
        host, port = StubAddressFactory()
        addr = Address.from_tuple((host, port))
        assert addr.host == host
        assert addr.port == port

    def test_from_path_constructor(self, faker):
        stub_address = StubAddressFactory()
        addr = Address.from_path(Path(StringAddressFactory.from_stub(stub_address)))
        assert addr.host == stub_address.host
        assert addr.port == stub_address.port

    def test_address_with_port_no_default(self, faker):
        stub_address = StubAddressFactory()
        addr = Address.parse_address(StringAddressFactory.from_stub(stub_address))
        assert addr.host == stub_address.host
        assert addr.port == stub_address.port

    def test_address_with_port_default(self, faker):
        host, port = StubAddressFactory()
        addr = Address.parse_address(host, default_port=port)
        assert addr.host == host
        assert addr.port == port

    def test_address_without_port_default(self, faker):
        domain, port = StubAddressFactory()
        addr = Address.parse_address(domain, default_port=port)
        assert addr.host == domain
        assert addr.port == port

    def test_address_without_port(self, faker):
        domain = faker.domain_name(3)
        with pytest.raises(ValueError):
            Address.parse_address(domain)

    def test_address_with_invalid_port(self, faker):
        with pytest.raises(ValueError):
            Address.parse_address(f"{faker.domain_name(3)}:{faker.pystr()}")

    def test_address_with_multiple_ports(self, faker):
        domain, port1, port2 = *StringAddressFactory().split(":"), faker.port_number()
        with pytest.raises(ValueError):
            Address.parse_address(f"{domain}:{port1}:{port2}")


class TestAddressIPResolving:
    @classmethod
    @pytest.fixture(autouse=True)
    def setup(cls, faker):
        cls.host_addr = AddressFactory()
        cls.ipv4_addr = Address(faker.ipv4(), faker.port_number())
        cls.ipv6_addr = Address(faker.ipv6(), faker.port_number())

    def test_ip_resolver_with_hostname(self):
        with patch("dns.resolver.resolve") as resolve:
            answer = MagicMock()
            answer.__str__.return_value = self.ipv4_addr.host
            resolve.return_value = [answer]

            resolved_ip = self.host_addr.resolve_ip(lifetime=3)

            resolve.assert_called_once_with(self.host_addr.host, RdataType.A, lifetime=3)
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == self.ipv4_addr.host

    @pytest.mark.asyncio
    async def test_async_ip_resolver_with_hostname(self):
        with patch("dns.asyncresolver.resolve") as resolve:
            answer = MagicMock()
            answer.__str__.return_value = self.ipv4_addr.host + "."
            resolve.return_value = [answer]

            resolved_ip = await self.host_addr.async_resolve_ip(lifetime=3)

            resolve.assert_called_once_with(self.host_addr.host, RdataType.A, lifetime=3)
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == self.ipv4_addr.host

    def test_ip_resolver_with_ipv4(self):
        with patch("dns.resolver.resolve") as resolve:
            resolved_ip = self.ipv4_addr.resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == self.ipv4_addr.host

    @pytest.mark.asyncio
    async def test_async_ip_resolver_with_ipv4(self):
        with patch("dns.asyncresolver.resolve") as resolve:
            resolved_ip = await self.ipv4_addr.async_resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == self.ipv4_addr.host

    def test_ip_resolver_with_ipv6(self):
        with patch("dns.resolver.resolve") as resolve:
            resolved_ip = self.ipv6_addr.resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv6Address)
            assert str(resolved_ip) == self.ipv6_addr.host

    @pytest.mark.asyncio
    async def test_async_ip_resolver_with_ipv6(self):
        with patch("dns.asyncresolver.resolve") as resolve:
            resolved_ip = await self.ipv6_addr.async_resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv6Address)
            assert str(resolved_ip) == self.ipv6_addr.host
