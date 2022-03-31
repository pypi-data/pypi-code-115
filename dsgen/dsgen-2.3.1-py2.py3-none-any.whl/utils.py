# -*- python3 -*-
#
# Copyright 2021, 2022 Cecelia Chen
# Copyright 2018, 2019, 2020, 2021 Xingeng Chen
# Copyright 2016, 2017, 2018 Liang Chen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.'''
#
# dsgen.utils

from .base import DSBase, CeleryHelper


class DSGenerator(DSBase):
    '''
    '''

    def __init__(self, json_path=None):
        '''
        :param json_path: (string)
        '''
        super(ve_config_klass, self).__init__()
        self.collect_apps()
        if json_path is not None:
            try:
                self.site_config = json.load(json_path)
            except Exception as e:
                from django.core.exceptions import ImproperlyConfigured
                msg = 'error raises when loading {fp}'.format(fp=json_path)
                bad_config = ImproperlyConfigured(msg)
                raise bad_config

#---eof---#
