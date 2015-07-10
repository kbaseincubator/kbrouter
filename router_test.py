import os
import router
import unittest
import tempfile
import time

class ProxyTestCase(unittest.TestCase):

    def setUp(self):
      self.app = router.app.test_client()
      self.service='transform'

    #def tearDown(self):
    #  print "No teardown"

    def test_list(self):
        rv = self.app.get('/services/')
        assert rv.status_code==200
        assert rv.data.rfind(self.service)

    def test_service(self):
        rv = self.app.delete('/kill/'+self.service)
        assert rv.status_code==200
        rv = self.app.get('/services/'+self.service+'/')
        assert rv.status_code==200

    def test_delete_service(self):
        rv = self.app.delete('/kill/'+self.service)
        assert rv.status_code==200

if __name__ == '__main__':
    unittest.main()
