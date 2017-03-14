import unittest
import sys
sys.path.append('..')

from patheng import utils


class Option43Test(unittest.TestCase):

    bs_test1 = '91094F7074696F6E2034350106546573742031'
    d_test1 = {
        145: 'Option 45',
        1: 'Test 1'
    }

    bs_test2 = '18094F7074696F6E20323417094F7074696F6E203233'
    d_test2 = {
        '23': 'Option 23',
        24: 'Option 24'
    }

    bs_test3 = '780A4F6E65207477656E74792C0B466F7572747920666F7572'
    d_test3 = {
        '120': 'One twenty',
        '44': 'Fourty four'
    }

    def test_to_option43(self):
        self.assertEqual(self.bs_test1, utils.to_option43(self.d_test1))
        self.assertEqual(self.bs_test2, utils.to_option43(self.d_test2))
        self.assertEqual(self.bs_test3, utils.to_option43(self.d_test3))

    def test_from_option43(self):
        self.assertEqual({int(k): v for k, v in self.d_test1.items()},
                         utils.from_option43(self.bs_test1))
        self.assertEqual({int(k): v for k, v in self.d_test2.items()},
                         utils.from_option43(self.bs_test2))
        self.assertEqual({int(k): v for k, v in self.d_test3.items()},
                         utils.from_option43(self.bs_test3))

if __name__ == '__main__':
    unittest.main()
