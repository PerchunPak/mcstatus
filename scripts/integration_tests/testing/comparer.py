from __future__ import annotations

import dataclasses
import typing as t

import typing_extensions as te


@dataclasses.dataclass(init=False)
class Difference:
    key: str
    one: t.Any
    two: t.Any

    def __init__(self, key: str, one: t.Any, two: t.Any, *, reverse: bool) -> None:
        self.key = key
        self.one = one if not reverse else two
        self.two = two if not reverse else one


@dataclasses.dataclass
class SubDifference:
    key: str
    value: LIST_OF_DIFFERENCES


LIST_OF_DIFFERENCES: te.TypeAlias = list[Difference | SubDifference]


class Comparer:
    def __init__(self, one: dict[str, t.Any], two: dict[str, t.Any]) -> None:
        self.one = one
        self.two = two

    def compare(self) -> LIST_OF_DIFFERENCES:
        if self.one == self.two:
            return []

        one_with_two = self._compare(self.one, self.two, reverse=False)
        two_with_one = self._compare(self.two, self.one, reverse=True)

        return self._merge_differences(one_with_two, two_with_one)

    @staticmethod
    def _compare(one: dict[str, t.Any], two: dict[str, t.Any], *, reverse: bool) -> LIST_OF_DIFFERENCES:
        differences: LIST_OF_DIFFERENCES = []
        for one_key, one_value in one.items():
            if one_key not in two:
                differences.append(Difference(one_key, one_value, None, reverse=reverse))
            elif isinstance(one_value, dict) and isinstance(two[one_key], dict):
                differences.append(SubDifference(one_key, Comparer._compare(one_value, two[one_key], reverse=reverse)))
            elif one_value != two[one_key]:
                differences.append(Difference(one_key, one_value, two[one_key], reverse=reverse))

        return differences

    def _merge_differences(self, one_with_two: LIST_OF_DIFFERENCES, two_with_one: LIST_OF_DIFFERENCES) -> LIST_OF_DIFFERENCES:
        for difference in one_with_two:
            if len((found := tuple(filter(lambda x: x.key == difference.key, two_with_one)))) > 0:
                (found,) = found
                if isinstance(difference, SubDifference) and isinstance(found, SubDifference):
                    new_sub_difference = self._merge_differences(difference.value, found.value)
                    difference.value = new_sub_difference
                two_with_one.remove(found)
        return one_with_two + two_with_one
