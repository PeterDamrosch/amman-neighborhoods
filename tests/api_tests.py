import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO,BytesIO

import sys; print(list(sys.modules.keys()))

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "hoods.config.TestingConfig"

from hoods import app

class TestAPI(unittest.TestCase):
    """ Tests for the hoods API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

    def test_post_point(self):
        a = {"lat": "31.954014","lng": "35.910794"}
        enteredName = "Somewhere else in Amman"
        enteredDescription = "Test works inshallah"
       
        data = {
            "coordinates": a,
            "description": enteredDescription,
            "name": enteredName
        }
        print(data)
        
        response = self.client.post("/api/geometry",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
    
    def test_post_point_schema_wrong(self):
        #Wrong form for point coordinate, should be dictionary/json object
        a = {"lat": 31.954014,"lng": 35.910794}
        enteredName = "Jabal Hussein Test"
        enteredDescription = "Test Input of Jabal Hussein"
       
        data = {
            "coordinates": a,
            "description": enteredDescription,
            "name": enteredName
        }
        print(data)
        
        response = self.client.post("/api/geometry",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
        )
        print(response.status_code)
        
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.mimetype, "application/json")
    
    def test_get_all_success(self):
        response = self.client.get("/api/geometry",
            headers=[("Accept", "application/json")]
        )
        print(response.status_code)
        print("Test response message")
        
        data = json.loads(response.data.decode("ascii"))
        print(data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["type"], "FeatureCollection")
    
    def test_get_5_success(self):
        response = self.client.get("/api/geometry",
            headers=[("Accept", "application/json")]
        )
        print(response.status_code)
        print("Test response message")
        
        data = json.loads(response.data.decode("ascii"))
        print(data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["type"], "FeatureCollection")
        