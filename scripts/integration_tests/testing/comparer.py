from __future__ import annotations

import dataclasses
import typing as t

import typing_extensions as te


@dataclasses.dataclass
class Difference:
    key: str
    one: list[Difference] | t.Any
    two: list[Difference] | t.Any


class Comparer:
    def __init__(self, one: dict[str, t.Any], two: dict[str, t.Any]) -> None:
        self.one = one
        self.two = two

    def compare(self) -> list[Difference]:
        if self.one == self.two:
            return []

        one_with_two = self._compare(self.one, self.two)
        two_with_one = self._compare(self.two, self.one)

        return self._merge_differences(one_with_two, two_with_one)

    @staticmethod
    def _compare(one: dict[str, t.Any], two: dict[str, t.Any]) -> list[Difference]:
        differences: list[Difference] = []
        for one_key, one_value in one.items():
            if one_key not in two:
                differences.append(Difference(one_key, one_value, None))
            elif isinstance(one_value, dict) and isinstance(two[one_key], dict):
                differences.append(Comparer._compare(one_value, two[one_key]))
            elif one_value != two[one_key]:
                differences.append(Difference(one_key, one_value, two[one_key]))

        return differences

    # TODO this thing doesn't work with recursive differences, fix it
    def _merge_differences(self, one_with_two: list[Difference], two_with_one: list[Difference]) -> list[Difference]:
        for difference in one_with_two:
            if all(isinstance(x, list) for x in [difference.one, difference.two]): ...
            if len((found := list(filter(lambda x: x.key == difference.key, two_with_one)))) > 0:
                if all(isinstance(x, list) for x in [difference.one, difference.two, found[0].one, found[0].two]):
                    difference.one = self._merge_differences(difference.one, found[0].one)
                    difference.two = self._merge_differences(difference.two, found[0].two)
                    continue
                two_with_one.remove(found[0])
        return one_with_two + two_with_one
