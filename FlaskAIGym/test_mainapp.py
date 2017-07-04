#! coding:utf-8
"""
test_flask_rest.py
http://momijiame.tumblr.com/post/39378516046/python-%E3%81%AE-flask-%E3%81%A7-rest-api-%E3%82%92%E4%BD%9C%E3%81%A3%E3%81%A6%E3%81%BF%E3%82%8B
"""

import json
import unittest

import mainapp as flask_app
from common_tools import StatusCodes, ContentType, JobState, ResultState


class FlaskrTestCase(unittest.TestCase):
    """ Flask Test """

    def setUp(self):
        self.app = flask_app.app.test_client()
        flask_app.app_init()

    def tearDown(self):
        pass

    def test_helth(self):
        """ test helth check """
        response = self.app.post('/health')
        self.assertEqual(response.status_code, 200)

    def test_api_get_invalid(self):
        response = self.app.get('/api/test_api_get_invalid')
        self.assertEqual(response.status_code, StatusCodes.NoContent)

    def test_api_post(self):
        """ test api post """
        content_body = json.dumps({'name': 'fifi', 'param_dir': '/tmp/'})
        response = self.app.post('/api/invalid_content_type',
                                 data=content_body,
                                 content_type=ContentType.application_json)  # invalid
        self.assertEqual(response.status_code, StatusCodes.OK200)

    def test_api_post_invalid_content_type(self):
        """ test api post """
        content_body = json.dumps({'name': 'fifi'})
        response = self.app.post('/api/invalid_content_type',
                                 data=content_body,
                                 content_type=ContentType.text_plain)  # invalid
        self.assertEqual(response.status_code, StatusCodes.BadRequest400)
        pass


class TestMultiProcess(unittest.TestCase):
    def setUp(self):
        self.app = flask_app.app.test_client()
        flask_app.app_init()

    def tearDown(self):
        pass

    def test_exist_mp_numbers(self):
        # Process Numbers
        response = self.app.post('/api/process/numbers')
        self.assertEqual(response.status_code, StatusCodes.OK200)

    def test_exist_mp_killAll(self):
        # Process Kill-All
        response = self.app.post('/api/process/killall')
        self.assertEqual(response.status_code, StatusCodes.OK200)

    def test_mp_numbers(self):
        # Process Numbers
        response = self.app.post('/api/process/numbers')
        self.assertEqual(response.status_code, StatusCodes.OK200)

        # Number is positive
        content_body_dict = json.loads(response.data.decode("utf-8"))
        mp_num = content_body_dict["numbers"]
        self.assertTrue(0 <= mp_num)


class TestPages(unittest.TestCase):
    def setUp(self):
        self.app = flask_app.app.test_client()
        flask_app.app_init()

    def test_statues(self):
        response = self.app.get('/')


if __name__ == '__main__':
    unittest.main()
