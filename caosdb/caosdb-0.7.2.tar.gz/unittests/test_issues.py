# This file is a part of the CaosDB Project.
#
# Copyright (c) 2022 IndiScale GmbH
# Copyright (c) 2022 Daniel Hornung (d.hornung@indiscale.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

"""Test known issues to prevent regressions.
"""

import os

import lxml
import caosdb as db

from pytest import raises


def test_issue_100():
    """_parse_value() fails for some list-valued content
    """

    # Parse from (invalid) XML file
    filename = os.path.join(os.path.dirname(__file__), "data", "list_in_value.xml")
    xml_el = lxml.etree.parse(filename).getroot()
    with raises(db.ServerConfigurationException) as exc_info:
        db.common.models._parse_single_xml_element(xml_el)
    assert "invalid XML: List valued properties" in exc_info.value.msg
