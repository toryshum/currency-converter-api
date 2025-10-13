from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch
from decimal import Decimal
import requests


class CostsConvertedAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('converter.views.get_exchange_rate_usd_to')
    @patch('converter.views.requests.get')
    def test_endpoint_with_mocked_data(self, mock_requests_get, mock_get_rate):
        mock_get_rate.return_value = Decimal('4.0')

        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "data": [
                {"campaign": "Test A", "cost_usd": 100},
                {"campaign": "Test B", "cost_usd": 50}
            ]
        }

        response = self.client.get('/api/costs/converted', {'currency': 'PLN'})

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['currency'], 'PLN')
        self.assertEqual(data['exchange_rate'], 4.0)
        self.assertEqual(len(data['data']), 2)

        self.assertEqual(data['data'][0]['cost_pln'], 400.0)
        self.assertEqual(data['data'][1]['cost_pln'], 200.0)

    @patch('converter.views.get_exchange_rate_usd_to')
    @patch('converter.views.requests.get')
    def test_endpoint_empty_data(self, mock_requests_get, mock_get_rate):
        mock_get_rate.return_value = Decimal('3.5')
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {"data": []}

        response = self.client.get('/api/costs/converted', {'currency': 'PLN'})
        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['data'], [])
        self.assertEqual(data['exchange_rate'], 3.5)

    @patch('converter.views.get_exchange_rate_usd_to')
    @patch('converter.views.requests.get')
    def test_endpoint_staging_error(self, mock_requests_get, mock_get_rate):
        mock_get_rate.return_value = Decimal('4.0')
        mock_requests_get.side_effect = requests.RequestException("Staging unreachable")

        response = self.client.get('/api/costs/converted', {'currency': 'PLN'})
        self.assertEqual(response.status_code, 502)
        self.assertIn('error', response.json())
