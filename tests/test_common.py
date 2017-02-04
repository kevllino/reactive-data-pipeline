from nose.tools import *
from lib.common import *
import json
import base64

class CommonFun(object):

    def test_base64(self):
        jobject = json.loads('{"build_id":"10.3.5.34","inst_id":"5ef0a5aa2ab8d1251296db5cc31d732109ba31428d030c9ca37df702de6c279","trialstate":"Expired","_l":32}')
        jencoded = "eyJidWlsZF9pZCI6IjEwLjMuNS4zNCIsImluc3RfaWQiOiI1ZWYwYTVhYTJhYjhkMTI1MTI5NmRiNWNjMzFkNzMyMTA5YmEzMTQyOGQwMzBjOWNhMzdkZjcwMmRlNmMyNzkiLCJ0cmlhbHN0YXRlIjoiRXhwaXJlZCIsIl9sIjozMn0NCg=="
        assert_equal(json.loads(base64.b64decode(jencoded)), jobject)
        print  "base64 enc / dec clarified"

    def test_remove_dict_element(self, sol):
        initial_dico = {'name': 'Kevin', 'age': 23}
        expected_dico = {'name': 'Kevin'}
        eq_(sol(initial_dico, 'age'), expected_dico)
        print "remove_dict_element works well"


# run tests
t = CommonFun()
t.test_base64()
t.test_remove_dict_element(remove_dict_element)