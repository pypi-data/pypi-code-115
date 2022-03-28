# -*- encoding: utf-8 -*-
#
# This file is a part of the CaosDB Project.
#
# Copyright (C) 2022 Indiscale GmbH <info@indiscale.com>
# Copyright (C) 2022 Timm Fitschen <f.fitschen@indiscale.com>
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
#
import caosdb as db
from lxml import etree


def test_parse_xml():
    # @review Florian Spreckelsen 2022-03-17
    xml_str = """
        <EntityACL>
          <Grant priority="False" role="role1">
            <Permission name="RETRIEVE:ENTITY"/>
          </Grant>
          <Deny priority="False" role="role1">
            <Permission name="RETRIEVE:ENTITY"/>
          </Deny>
          <Grant priority="True" role="role1">
            <Permission name="RETRIEVE:ENTITY"/>
          </Grant>
          <Deny priority="True" role="role1">
            <Permission name="RETRIEVE:ENTITY"/>
          </Deny>
        </EntityACL>"""
    xml = etree.fromstring(xml_str)
    left_acl = db.ACL(xml)

    right_acl = db.ACL()
    right_acl.grant(role="role1", permission="RETRIEVE:ENTITY",
                    revoke_denial=False)
    right_acl.deny(role="role1", permission="RETRIEVE:ENTITY",
                   revoke_grant=False)
    right_acl.grant(role="role1", permission="RETRIEVE:ENTITY",
                    priority=True, revoke_denial=False)
    right_acl.deny(role="role1", permission="RETRIEVE:ENTITY",
                   priority=True, revoke_grant=False)

    assert left_acl == right_acl
