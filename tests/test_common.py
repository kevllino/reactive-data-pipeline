from nose.tools import assert_equal
import json
import base64

class JsonEncodingDeconding(object):

    def test(self):
        jobject = json.loads('{"build_id":"10.3.5.34","inst_id":"5ef0a5aa2ab8d1251296db5cc31d732109ba31428d030c9ca37df702de6c279","trialstate":"Expired","_l":32}')
        jencoded = "eyJidWlsZF9pZCI6IjEwLjMuNS4zNCIsImluc3RfaWQiOiI1ZWYwYTVhYTJhYjhkMTI1MTI5NmRiNWNjMzFkNzMyMTA5YmEzMTQyOGQwMzBjOWNhMzdkZjcwMmRlNmMyNzkiLCJ0cmlhbHN0YXRlIjoiRXhwaXJlZCIsIl9sIjozMn0NCg=="
        assert_equal(json.loads(base64.b64decode(jencoded)), jobject)

        print 'ALL TESTS PASSED'

# run tests
t = JsonEncodingDeconding()
t.test()