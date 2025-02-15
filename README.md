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

### Project Structure
```
/your-project-root/
    ├── flask_app.py          # Main application file
    ├── static/
    │   ├── css/
    │   │   └── styles.css
    │   ├── js/
    │   │   └── script.js
    │   └── robots.txt
    ├── templates/
    │   └── index.html
    ├── logs/                 # Created automatically
    │   └── pdftoolkit.log
    └── requirements.txt
```

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

### PythonAnywhere Deployment

1. Upload your files to PythonAnywhere
2. Configure your web app:
   - Working directory: `/home/yourusername/mysite`
   - WSGI configuration file: Update paths in the WSGI file
   - Static files:
     ```
     URL: /static/
     Directory: /home/yourusername/mysite/static
     ```

3. Install requirements:
```sh
pip3 install --user -r requirements.txt
```

4. Reload your web app

### Running Locally

Development server:
```sh
python flask_app.py
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

## 🔒 Security

- All file processing is done in memory
- No files are stored on the server
- Input validation on both client and server side
- Rate limiting to prevent abuse
- File type and size restrictions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**wanazhar** - [GitHub Profile](https://github.com/wanazhar)

## 🌐 Live Demo

Try it out: [PDFToolkit on PythonAnywhere](https://wanazhar.pythonanywhere.com)

---

<p align="center">Made with ❤️ by <a href="https://github.com/wanazhar">wanazhar</a></p>
