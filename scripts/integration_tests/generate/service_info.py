import dataclasses
import typing as t

import typing_extensions as te

from .models import MinecraftCoreData


@dataclasses.dataclass
class ServiceInfo:
    id: str
    image: str
    env: dict[str, str] | None
    options: list[str] | None
    expected: dict[str, t.Any]

    @classmethod
    def from_dict(cls, data: MinecraftCoreData) -> list[te.Self]:
        output: list[ServiceInfo] = []
        if "versions" in data:
            assert len(data["versions"]) > 0 and data["image"] == "itzg/minecraft-server"
        else:
            data["versions"] = [None]

        for version in data["versions"]:
            id = data["id"] + (f"-{version}" if version else "")

            if version:
                data.setdefault("env", {})
                data["env"]["VERSION"] = version

            if data["image"] == "itzg/minecraft-server":
                data.setdefault("env", {})
                data["env"]["EULA"] = "TRUE"

            output.append(
                cls(
                    id=id,
                    image=data["image"],
                    env=data.get("env"),
                    options=data.get("options"),
                    expected=data["expected"][version] if version else data["expected"],
                )
            )

        return output

    def attach_port(self, port: int) -> None:
        if self.image == "itzg/minecraft-server":
            self.env = {} if self.env is None else self.env
            self.env["SERVER_PORT"] = str(port)
        else:
            assert self.env is not None
            for key, value in self.env.items():
                self.env[key] = value.replace("{{ PORT }}", str(port))

    def to_yaml(self) -> str:
        output = f"{self.id}:\n"
        output += f"  image: {self.image}\n"

        if self.env:
            output += "  env:\n"
            for key, value in self.env.items():
                output += f"    {key}: {value}\n"

        if self.options:
            output += "  options: >-\n    "
            output += "\n    ".join(self.options) + "\n"

        return output
