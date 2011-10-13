import unittest

def main():
   runner = unittest.TextTestRunner()
   test_suite = suite()
   runner.run (test_suite)

if __name__ == '__main__':

   main()
