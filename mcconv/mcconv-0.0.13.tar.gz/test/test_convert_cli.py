# 1.0187707208460053e+00 3.2168693465909212e-02 4.0978586064750729e+01 4.1001997452143407e+01 9.3827000000000005e-01
# 1.0254104367327128e+00 -2.1977682486632854e-02 4.0980287617715881e+01 4.1003856811352591e+01 9.3827000000000005e-01
# 1.0290925649513989e+00 -1.0264105661284585e-03 4.0977975826623556e+01 4.1001632723600189e+01 9.3827000000000005e-01

import os
import unittest
from mcconv import detect_mc_type, apply_crossing_angle
from pyHepMC3 import HepMC3 as hm


class TestConvertCli(unittest.TestCase):

    def setUp(self) -> None:
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.data_path = os.path.join(dir_path, 'data')

    def _get_file_path(self, path):
        """Gets data file path"""
        return os.path.join(self.data_path, path)


    def test_convert_gemc(self):
        """Test detecting BeaGLE file type"""

        evt = hm.GenEvent(hm.Units.GEV, hm.Units.MM)