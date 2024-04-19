import pytest
from flask import Flask
from flask.testing import FlaskClient
import requests

API_URL = 'http://localhost:3000/api'

def test_items_get():
    # Send a GET request to fetch the user
    response = requests.get(f'{API_URL}/items/get/')
    assert response.status_code == 200
    actual_items_data = response.json()
    assert 'items' in actual_items_data
    items = actual_items_data['items']
    assert isinstance(items, list)
    assert len(actual_items_data) > 0
    item_array = items[0]
    for item in items:
        assert 'item' in item_array
        assert 'category' in item_array
        assert 'in stock' in item_array

