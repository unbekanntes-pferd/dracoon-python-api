""" 
DRACOON Python API 
Test runner 
Runs all tests set up in /tests directory

Octavio Simone, October 2022
"""

import unittest

loader = unittest.TestLoader()
tests = loader.discover('./tests', 'test_*.py')

runner = unittest.runner.TextTestRunner()

if __name__ == "__main__":
    runner.run(tests)