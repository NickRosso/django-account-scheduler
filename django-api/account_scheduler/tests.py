from django.test import TestCase
from django.urls import reverse, resolve
import requests
class TestUrls:
    
    def test_post_photo_url(self):
        path = reverse('photo', kwargs={'pk':1}) 
        assert resolve(path).view_name == "Photo"

    def test_photo_get_url(self):
        response = requests.get("http://localhost:8000/photo")
        assert response.status_code == 200
