# 📄 PDF Toolkit - Web-Based PDF Processor

A secure and feature-rich **Flask-based web application** that provides an easy-to-use interface for PDF operations. 🚀

## ✨ Features

### Core PDF Operations
- 🔐 **Encrypt PDFs** - Secure PDFs with password protection
- 🔓 **Decrypt PDFs** - Remove password protection (with correct password)
- 🔗 **Merge PDFs** - Combine multiple PDFs into one
- ✂️ **Split PDFs** - Extract pages by range or interval
- 📉 **Compress PDFs** - Reduce file size while maintaining quality
- 📝 **Extract Text** - Convert PDF content to text
- 🖼️ **Extract Images** - Save all images from PDFs
- 🔍 **OCR Processing** - Convert scanned PDFs to searchable text
- 🔄 **Rearrange Pages** - Reorder pages within a PDF

### Security Features
- 🛡️ Rate limiting protection
- 🔒 File type validation
- 📊 File size restrictions (100MB max)
- 🚫 Robot exclusion support
- 📝 Comprehensive logging

### User Experience
- 💫 Loading indicators
- ⚠️ Clear error messages
- ✅ Client-side validation
- 🎯 Responsive design
- 📱 Mobile-friendly interface

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- pip (Python package manager)
- tesseract-ocr (for OCR functionality)

### Installation

1. Clone the repository:
```sh
git clone https://github.com/wanazhar/pdftoolkit.git
cd pdftoolkit
```

2. Create and activate virtual environment (recommended):
```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```sh
pip install -r requirements.txt
```

4. Install Tesseract OCR:
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS**: `brew install tesseract`

### Configuration

Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
MAX_CONTENT_LENGTH=104857600  # 100MB in bytes
```

### Running the Application

Development server:
```sh
python app.py
```

Production server (using gunicorn):
```sh
gunicorn app:app
```

Visit `http://127.0.0.1:5000` in your browser.

## 🔧 API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST` | `/encrypt` | Encrypt PDFs with password | 10/minute |
| `POST` | `/decrypt` | Decrypt password-protected PDFs | 10/minute |
| `POST` | `/merge` | Merge multiple PDFs | 10/minute |
| `POST` | `/split` | Split PDF into ranges | 10/minute |
| `POST` | `/compress` | Reduce PDF file size | 10/minute |
| `POST` | `/extract_text` | Extract text from PDF | 10/minute |
| `POST` | `/extract_images` | Extract images from PDF | 10/minute |
| `POST` | `/ocr` | Process scanned PDFs with OCR | 5/minute |
| `POST` | `/rearrange` | Reorder PDF pages | 10/minute |

## 🧪 Testing

Run the test suite:
```sh
python -m pytest
```

## 📦 Dependencies

Key dependencies (see `requirements.txt` for full list):
- Flask==2.0.1
- pikepdf==5.1.0
- PyMuPDF==1.19.1
- Pillow==9.0.0
- pytesseract==0.3.8
- Flask-Limiter==2.4.0
- pytest==7.0.0
- gunicorn==20.1.0

## 🔒 Security

- All file processing is done in memory
- No files are stored on the server
- Input validation on both client and server side
- Rate limiting to prevent abuse
- File type and size restrictions

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**wanazhar** - [GitHub Profile](https://github.com/wanazhar)

## 🌐 Live Demo

Try it out: [PDFToolkit on PythonAnywhere](https://wanazhar.pythonanywhere.com)

---

Made with ❤️ by wanazhar
