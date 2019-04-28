#!/usr/bin/env python
#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Frédéric Rodrigo 2017                                      ##
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

import json
from .Analyser_Merge_Dynamic import Analyser_Merge_Dynamic, SubAnalyser_Merge_Dynamic
from .Analyser_Merge import Source, CSV, Load, Mapping, Select, Generate
from .Analyser_Merge_Mapillary import Source_Mapillary
from time import gmtime, strftime

import time, os, shutil, hashlib, codecs, tempfile
from io import open # In python3 only, this import is not required
from backports import csv # In python3 only just "import csv"
from modules import config
from modules.PointInPolygon import PointInPolygon
from modules import SourceVersion
from modules import downloader


class Analyser_Merge_Traffic_Signs(Analyser_Merge_Dynamic):

    def check_not_only_for(self, not_for, only_for):
        country = "country" in self.config.options and self.config.options["country"]
        if only_for:
            return country and any(map(lambda co: country.startswith(co), only_for))
        if not_for:
            return not country or not any(map(lambda co: country.startswith(co), not_for))
        return True

    def dict_replace(self, d, f, r):
        return dict(map(lambda kv: [kv[0], kv[1] and kv[1].replace(f, r)], d.items()))

    def __init__(self, config, logger = None):
        Analyser_Merge_Dynamic.__init__(self, config, logger)
        if "country" not in self.config.options:
            return

        speed_limit_unit = self.config.options.get("speed_limit_unit")

        mapping = 'merge_data/mapillary-traffic-signs.mapping.json'
        mapingfile = json.loads(open(mapping).read())
        for r in mapingfile:
            if self.check_not_only_for(r.get('not_for'), r.get('only_for')):
                if speed_limit_unit:
                    unit = ' ' + speed_limit_unit
                else:
                    unit = ''
                r['select_tags'] = list(map(lambda select: self.dict_replace(select, '{speed_limit_unit}', unit), r['select_tags']))
                r['generate_tags'] = self.dict_replace(r['generate_tags'], '{speed_limit_unit}', unit)

                self.classFactory(SubAnalyser_Merge_Traffic_Signs, r['class'], r['class'], r['level'], r['otype'], r['conflation'], r['title'], r['object'], r['select_tags'], r['generate_tags'], mapping, 'trafficsigns')


class SubAnalyser_Merge_Traffic_Signs(SubAnalyser_Merge_Dynamic):
    def __init__(self, config, error_file, logger, classs, level, otype, conflation, title, object, selectTags, generateTags, mapping, layer):
        self.missing_official = {"item":"8300", "class": classs, "level": level, "tag": ["merge", "leisure"], "desc": T_f(u"{0} Traffic signs for {1} observed around but not associated tags", ', '.join(map(lambda kv: '%s=%s' % (kv[0], kv[1] if kv[1] else '*'), generateTags.items())), title) }
        SubAnalyser_Merge_Dynamic.__init__(self, config, error_file, logger,
            "www.mapillary.com",
            u"Traffic Signs from Street-level imagery",
            CSV(Source_Mapillary(attribution = u"Mapillary Traffic Signs", country = config.options['country'], polygon_id = config.polygon_id, logger = logger, mapping = mapping, layer = layer)),
            Load("X", "Y",
                select = {"value": object}),
            Mapping(
                select = Select(
                    types = otype,
                    tags = selectTags),
                conflationDistance = conflation,
                generate = Generate(
                    static1 = dict(filter(lambda kv: kv[1], generateTags.items())),
                    static2 = {"source": self.source},
                    mapping1 = {
                      "mapillary": "image_key",
                      "survey:date": lambda res: res["last_seen_at"][0:10]},
                text = lambda tags, fields: {"en": (
                    "Observed between %s and %s" % (fields["first_seen_at"][0:10], fields["last_seen_at"][0:10]) if fields["first_seen_at"][0:10] != fields["last_seen_at"][0:10] else
                    "Observed on %s" % (fields["first_seen_at"][0:10],))} )))
