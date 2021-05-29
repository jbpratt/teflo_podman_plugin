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
Pykwalify extensions module.

Module containing custom validation functions used for schema checking.
:copyright: (c) 2020 Red Hat, Inc.
:license: GPLv3, see LICENSE for more details.
"""
from typing import Sequence

from pykwalify.rule import Rule


def valid_volume_path(value: Sequence[str], obj_rule: Rule, path: str) -> bool:
    return any(
        len(v.split(":")) < 2
        for v in value
    )
