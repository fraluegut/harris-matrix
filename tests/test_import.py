import unittest

import harris_matrix


class ImportTest(unittest.TestCase):
    def test_version(self):
        self.assertRegex(harris_matrix.__version__, r"^\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
