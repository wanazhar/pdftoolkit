import unittest
import io
from flask_app import app

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

    def test_rotate_no_file(self):
        response = self.client.post('/rotate', data={'degree': 90})
        self.assertEqual(response.status_code, 400)

    def test_watermark_no_text(self):
        response = self.client.post('/watermark', data={
            'pdf': (io.BytesIO(b"%PDF-1.4\n%..."), 'test.pdf')
        })
        self.assertEqual(response.status_code, 400)

    def test_pdf_to_images_no_file(self):
        response = self.client.post('/pdf_to_images', data={})
        self.assertEqual(response.status_code, 400)

    def test_images_to_pdf_no_files(self):
        response = self.client.post('/images_to_pdf', data={})
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
