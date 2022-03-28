from sigur_worker.main import GateReal, GateTest
import unittest


class TestCase(unittest.TestCase):
    inst = GateReal(ip='192.168.100.109',
                    port=3312,
                    point_num=2)
    res = inst.make_connection()
    print("AUTH RES", res)

    @unittest.SkipTest
    def test_get_status(self):
        res = self.inst.get_status()
        self.assertEqual(res, 'ONLINE_NORMAL')

    def test_close(self):
        self.inst.close()
        res = self.inst.get_status()
        self.assertEqual(res, 'ONLINE_LOCKED')

    @unittest.SkipTest
    def test_open(self):
        self.inst.open()
        res = self.inst.get_status()
        self.assertEqual(res, 'ONLINE_UNLOCKED')


if __name__ == '__main__':
    unittest.main()
