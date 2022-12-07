"""Module with some factories used in tests."""
import datetime
import typing
import warnings

import factory
import factory.fuzzy
from faker import Faker
from mcstatus.address import Address
from dataclasses import dataclass
from collections.abc import Iterable

faker = Faker()


@dataclass
class StubAddress:
    host: str
    port: int

    def __iter__(self) -> Iterable:
        return iter((self.host, self.port))


class StubAddressFactory(factory.Factory):
    class Meta:
        model = StubAddress

    host = factory.fuzzy.FuzzyAttribute(lambda: faker.domain_name(levels=3))
    port = factory.fuzzy.FuzzyAttribute(faker.port_number)


class StringAddressFactory(StubAddressFactory):
    class Meta:
        model = str

    @classmethod
    def _create(cls, _: type[str], *, host: str, port: int) -> str:
        return f"{host}:{port}"

    @classmethod
    def from_stub(cls, stub: StubAddress) -> str:
        return cls._create(str, host=stub.host, port=stub.port)


class AddressFactory(StubAddressFactory):
    class Meta:
        model = Address
