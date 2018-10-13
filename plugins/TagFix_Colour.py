#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Noémie Lehuby 2018                                         ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

from plugins.Plugin import Plugin

try:
    from webcolors import name_to_hex, normalize_hex
    module_webcolors = True
except ImportError, e:
    print(e)
    module_webcolors = False

OSMOSE_CLASS = 32501
OSMOSE_CLASS_PT = 32502


class TagFix_Colour(Plugin):

    def init(self, logger):
        if not module_webcolors:
            return False
        Plugin.init(self, logger)
        self.errors[OSMOSE_CLASS] = {"item": 3250, "level": 3, "tag": ["value", "fix:chair"], "desc": T_(u"Invalid Colour")}
        self.errors[OSMOSE_CLASS_PT] = {"item": 3250, "level": 3, "tag": ["value", "fix:chair", "public_transport"], "desc": T_(u"Invalid Colour")}


def error_on_colour_tag(colour_tag, colour_tag_key, osmose_class):
    try:
        name_to_hex(colour_tag)
    except ValueError as e:
        # this is not a valid CSS color, maybe it's a RGB one
        try:
            if not colour_tag.startswith("#"):
                colour_tag = "#" + colour_tag
                missing_hash = True
            normalize_hex(colour_tag)
        except ValueError as ee:
            # this is not a valid RGB hex color either
            return {"class": osmose_class, "subclass": 1}

    if missing_hash:
        return {"class": osmose_class, "subclass": 2, 'fix': {colour_tag_key: "#" + colour_tag}}

    def check_tags(self, tags, osmose_class):
        err = []
        if "colour" in tags:
            err += error_on_colour_tag(tags["colour"], "colour", osmose_class)
        if "ref:colour_tx" in tags:
            err += error_on_colour_tag(tags["ref:colour_tx"],
                                       "ref:colour_tx", osmose_class)
        if "ref:colour" in tags:
            err += error_on_colour_tag(tags["ref:colour"],
                                       "ref:colour", osmose_class)
        if "building:colour" in tags:
            err += error_on_colour_tag(tags["building:colour"],
                                       "building:colour", osmose_class)
        if "roof:colour" in tags:
            err += error_on_colour_tag(tags["roof:colour"],
                                       "roof:colour", osmose_class)

        if err:
            return err

    def node(self, data, tags):
        return self.check_tags(tags, OSMOSE_CLASS)

    def way(self, data, tags, nds):
        return self.check_tags(tags, OSMOSE_CLASS)

    def relation(self, data, tags, members):
        if tags["type"] in ["route", "route_master"]:
            return self.check_tags(tags, OSMOSE_CLASS_PT)
        return self.check_tags(tags, OSMOSE_CLASS)


###########################################################################
from plugins.Plugin import TestPluginCommon


class Test(TestPluginCommon):
    def setUp(self):
        TestPluginCommon.setUp(self)
        self.p = TagFix_Colour(None)
        self.p.init(None)

    def test(self):
        self.check_err(self.p.node(None, {"colour": "jaune"}))
        self.check_err(self.p.way(None, {"colour": "0000ff"}, None))
        assert not self.p.relation(None, {"colour": "red"}, None)
        assert not self.p.way(None, {"colour": "grey"}, None)
        assert not self.p.way(None, {"colour": "gray"}, None)
        assert not self.p.way(None, {"colour": "lightgreen"}, None)
        assert not self.p.node(None, {"colour": "#808000"}, None)
        assert not self.p.way(None, {"colour": "#8080AA"}, None)
        assert not self.p.node(None, {"colour": "#FF0"}, None)
        assert not self.p.relation(None, {"colour": "#f00"}, None)
        assert not self.p.node(None, {"colour": "#a2bd31"}, None)
        # TODO : ajouter aussi sur d'autres tags colour
