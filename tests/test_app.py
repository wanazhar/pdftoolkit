import unittest
import io
from app import app

class TestPDFToolkit(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
    def test_encrypt_no_file(self):
        response = self.client.post('/encrypt', data={
            'password': 'test123'
        })
        self.assertEqual(response.status_code, 400)
        
    def test_encrypt_no_password(self):
        response = self.client.post('/encrypt', data={
            'pdfs': (io.BytesIO(b"test pdf content"), 'test.pdf')
        })
        self.assertEqual(response.status_code, 400)
        
    def test_invalid_file_type(self):
        response = self.client.post('/encrypt', data={
            'pdfs': (io.BytesIO(b"test content"), 'test.txt'),
            'password': 'test123'
        })
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main() 