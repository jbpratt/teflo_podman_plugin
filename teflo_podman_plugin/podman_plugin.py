#
# Copyright (C) 2020 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Teflo Podman provisioner plugin.

:copyright: (c) 2020 Red Hat, Inc.
:license: GPLv3, see LICENSE for more details.
"""
import os
import shutil
import subprocess
from typing import Dict
from typing import List

from teflo.core import ProvisionerPlugin
from teflo.exceptions import TefloProvisionerError
from teflo.helpers import schema_validator
from teflo.resources import Asset


class PodmanProvisionerPlugin(ProvisionerPlugin):
    __plugin_name__ = "podman"
    __schema_file_path__ = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "files/schema.yml",
        ),
    )
    __schema_ext_path__ = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "files/schema_extensions.py",
        ),
    )
    _exe: List[str]

    def __init__(self, asset: Asset):
        super().__init__(asset)

        self.create_logger(
            name=self.__plugin_name__,
            data_folder=self.config.get("DATA_FOLDER"),
        )

        exe_path = self.provider_params.get("executable_path")
        if exe_path:
            if not os.path.isfile(exe_path):
                raise TefloProvisionerError(
                    f"provided executable not found: {exe_path}",
                )
        else:
            exe_path = shutil.which("podman")
            if not exe_path or exe_path == "":
                raise TefloProvisionerError("failed to find podman executable")

        self._exe = [exe_path]

        remote = self.provider_params.get("remote")
        if remote:
            self._exe.extend(["--remote", "-c", remote["user"]])
            info = subprocess.check_output((*self._exe, "info")).decode().strip()
            self.logger.debug(info)

    def create(self) -> List[Dict[str, str]]:
        remote = self.provider_params.get("remote")
        if remote:
            subprocess.check_output(
                (
                    *self._exe,
                    "system",
                    "connection",
                    "add",
                    remote["user"],
                    "--identity",
                    remote["identity"],
                    remote["uri"],
                ),
            )

        run_command = [*self._exe, "run", "--detach"]
        if self.provider_params.get("privileged", False):
            run_command.append("--privileged")

        if self.provider_params.get("tty", True):
            run_command.append("--tty")

        container_name = self.provider_params.get("container_name")
        if container_name:
            run_command.append(f"--name={container_name}")

        for env_var in self.provider_params.get("environment", []):
            run_command.append(f'--env="{env_var}"')

        network_mode = self.provider_params.get("network_mode", "bridge")
        run_command.append(f"--network={network_mode}")

        for port in self.provider_params.get("ports", []):
            run_command.append(f"--publish={port}")

        caps = self.provider_params.get("capabilities", {})
        for cap in caps.get("add", []):
            run_command.append(f"--cap-add={cap}")
        for cap in caps.get("drop", []):
            run_command.append(f"--cap-drop={cap}")

        for volume in self.provider_params.get("volumes", []):
            src, dest = volume.split(":", 1)
            if not os.path.exists(src):
                os.makedirs(src)
            run_command.append(f"--volume={volume}")

        for arg in self.provider_params.get("additional_args", []):
            run_command.extend(arg.split(" "))

        run_command.append(self.provider_params["image"])
        entrypoint = self.provider_params.get("entrypoint")
        if entrypoint:
            run_command.append(entrypoint)

        container_id = subprocess.check_output(tuple(run_command)).decode().strip()
        if not container_name:
            container_name = (
                subprocess.check_output(
                    (
                        *self._exe,
                        "container",
                        "inspect",
                        "--format",
                        "{{.Name}}",
                        container_id,
                    ),
                )
                .decode()
                .strip()
            )

        res = {"name": self.asset.name, "ip": container_name, "asset_id": container_id}
        self.logger.info(res)
        return [res]

    def delete(self) -> None:
        subprocess.check_output((*self._exe, "rm", "-f", self.asset.asset_id))

    def authenticate(self) -> None:
        subprocess.check_output(
            (
                *self._exe,
                "login",
                f'-u={self.provider_credentials["username"]}',
                f'-p={self.provider_credentials["password"]}',
                self.provider_credentials["registry"],
            ),
        )

    def validate(self) -> None:
        schema_validator(
            schema_data=self.build_profile(self.asset),
            schema_files=[self.__schema_file_path__],
            schema_ext_files=[self.__schema_ext_path__],
        )
