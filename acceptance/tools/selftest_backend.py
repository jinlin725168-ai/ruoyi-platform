"""Executor self-test: the base platform boots and the auth/permission plumbing works."""

import unittest

from ruoyi_client import ApiError, Client


class BackendHealth(unittest.TestCase):
    def test_login_and_authenticated_call(self):
        client = Client()
        info = client.login()
        self.assertTrue(info["access_token"])
        me = client.get("/system/user/getInfo")
        self.assertEqual(me["data"]["user"]["userName"], "admin")

    def test_unauthenticated_call_is_rejected(self):
        client = Client()
        with self.assertRaises(ApiError) as caught:
            client.get("/system/user/getInfo")
        self.assertEqual(caught.exception.body.get("code"), 401)


if __name__ == "__main__":
    unittest.main()
