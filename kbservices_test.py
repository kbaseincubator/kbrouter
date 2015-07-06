import os
import kbservices
import unittest
import tempfile

class ProxyTestCase(unittest.TestCase):

    def setUp(self):
      self.s = kbservices.kbservices()
      self.service='Transform'
      self.bad_service='Bogus'

    def tearDown(self):
      self.s.kill_service(self.service)

    def test_isaservice(self):
      assert self.s.isaservice(self.service) is True

    def test_start_service(self):
      assert self.s.start_service(self.service) is True

    def test_bad_service(self):
      assert self.s.start_service(self.bad_service) is False

    def test_kill_service(self):
      assert self.s.start_service(self.service) is True
      assert self.s.kill_service(self.service) is True
      assert self.s.kill_service(self.service) is False

    def test_gethostport(self):
      self.s.start_service(self.service)
      (h,p)=self.s.get_hostport(self.service)
      assert h is not None
      assert p is not None

    def test_update_services(self):
      self.s.update_services()

    def test_get_list(self):
      l=self.s.get_list()
      assert type(l) is list
        

if __name__ == '__main__':
    unittest.main()

    def test_kill_service(self):
      self.s.kill_service(self.service)

    def test_gethostport(self):
      self.s.start_service(self.service)
      (h,p)=self.s.get_hostport(self.service)
      assert h is not None
      assert p is not None

    def test_update_services(self):
      self.s.update_services()

    def test_get_list(self):
      l=self.s.get_list()
      assert type(l) is list
        

if __name__ == '__main__':
    unittest.main()
