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
    :copyright: (c) 2020 Red Hat, Inc.
    :license: GPLv3, see LICENSE for more details.
"""
import os
from typing import Any
from typing import Dict
from typing import List

from podman import PodmanClient
from teflo.core import ProvisionerPlugin
from teflo.exceptions import TefloProvisionerError
from teflo.helpers import schema_validator


class PodmanProvisionerPlugin(ProvisionerPlugin):
    __plugin_name__ = 'podman'

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
    _podman: PodmanClient

    def __init__(self, asset):
        super().__init__(asset)

        self.create_logger(
            name=self.__plugin_name__,
            data_folder=self.config.get('DATA_FOLDER'),
        )

        uri = self.provider_params.get("uri")
        if uri:
            self._podman = PodmanClient(base_url=uri)
        else:
            # check for default podman sock, error out if service not started
            # or try to start it?
            self._podman = PodmanClient()

        if not self._podman.ping():
            raise TefloProvisionerError("Failed to ping the podman server")

    def __del__(self):
        self._podman.close()

    def create(self) -> List[Dict[str, str]]:
        container = self._podman.containers.run(
            detach=True,
            environment=self.provider_params.get("environment", {}),
            image=self.provider_params["image"],
            mounts=[
                {"target": v["target"], "source": v["source"], "type": v.get("type", "volume")}
                for v in self.provider_params.get("mounts", [])
            ],
            name=self.asset.name.replace(" ", "-"),
            network_mode=self.provider_params.get("network_mode", "bridge"),
            ports=self.provider_params.get("ports", {}).items(),
            privileged=self.provider_params.get("privileged", False),
            tty=self.provider_params.get("tty", True),
        )

        return [{"name": container.name, "ip": container.name, "asset_id": container.id}]

    def delete(self) -> None:
        if self.provider_params.get("remove", True):
            self._podman.containers.get(self.asset.asset_id).remove(force=True)

    def authenticate(self):
        if self.provider_credentials:
            self._podman.login(
                username=self.provider_credentials["username"],
                password=self.provider_credentials["password"],
                registry=self.provider_credentials["registry"],
            )
        else:
            self.logger.warning("No credentials were provided, continuing unauthenticated")

    def validate(self):
        schema_validator(
            schema_data=self.build_profile(self.asset),
            schema_files=[self.__schema_file_path__],
            schema_ext_files=[self.__schema_ext_path__],
        )
