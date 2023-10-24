import json
import unittest
from unittest.mock import patch
from app import app

class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch('app.requests.get')  # Mock the requests.get method
    def test_index_route(self, mock_get):
        f = open('Help/testdata.json')
 
        # returns JSON object as 
        # a dictionary
        data = json.load(f)
        
        # Mock API response
        mock_response = data
        # Set up the mock response
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status.return_value = None

        # Simulate a POST request with JSON data
        response = self.app.post('/', json=mock_response)

        # Assert the status code
        self.assertEqual(response.status_code, 200)

        # Assert that the session data is set correctly
        with app.test_request_context('/'):
            assert 'data' in app.session
            self.assertEqual(app.session['data'], mock_response)

        # Assert that the template is rendered with the correct data
        self.assertIn(b'example', response.data)

    def test_index_route_get_request(self):
        # Simulate a GET request
        response = self.app.get('/')

        # Assert the status code
        self.assertEqual(response.status_code, 200)

        # Assert that the template is rendered without data
        self.assertNotIn(b'example', response.data)

if __name__ == '__main__':
    unittest.main()