# 📄 PDF Toolkit - Web-Based PDF Processor  

A simple **Flask-based web application** that provides an easy-to-use interface for various **PDF operations**, including **encryption, decryption, merging, splitting, and compression**. 🚀  

## ✨ Features  

✔ **Encrypt PDFs** - Secure your PDFs with a password  
✔ **Decrypt PDFs** - Remove password protection (with the correct password)  
✔ **Merge PDFs** - Combine multiple PDFs into one  
✔ **Split PDFs** - Extract specific pages from a PDF  
✔ **Compress PDFs** - Reduce PDF file size while maintaining quality  

---

## 📂 Folder Structure  

```
📁 pdf-toolkit/
│── 📄 app.py          # Main Flask application  
│── 📄 requirements.txt # Dependencies  
│── 📁 templates/      # HTML frontend files  
│── 📁 static/         # CSS, JS, and other assets  
│── 📁 uploads/        # Temporary storage for uploaded files  
```

---

## 🚀 Getting Started  

### 🔹 1. Prerequisites  

Ensure you have **Python 3.7+** installed. You also need **pip** for package management.  

### 🔹 2. Installation  

Clone the repository and install dependencies:  

```sh
git clone https://github.com/yourusername/pdf-toolkit.git
cd pdf-toolkit
pip install -r requirements.txt
```

### 🔹 3. Run the Application  

Start the Flask server:  

```sh
python app.py
```

Visit **http://127.0.0.1:5000/** in your browser to use the web app! 🌍  

---

## 🛠️ API Endpoints  

| Method | Endpoint     | Description |
|--------|-------------|-------------|
| `POST` | `/encrypt`  | Encrypts uploaded PDFs with a password |
| `POST` | `/decrypt`  | Decrypts password-protected PDFs |
| `POST` | `/merge`    | Merges multiple PDFs into one |
| `POST` | `/split`    | Splits a PDF into specific page ranges |
| `POST` | `/compress` | Compresses PDF file size |

### 📝 Example Usage (cURL)  

```sh
curl -X POST -F "pdfs=@file.pdf" -F "password=1234" http://127.0.0.1:5000/encrypt -o encrypted.zip
```

---

## 🏗️ Built With  

- **Flask** - Lightweight web framework  
- **pikepdf** - Powerful PDF manipulation library  
- **HTML, CSS, JavaScript** - Frontend interface  

---

## 📜 License  

This project is licensed under the **MIT License**. Feel free to use and modify it as needed!  

👨‍💻 **Sample**: [wanazhar on PythonAnywhere](https://wanazhar.pythonanywhere.com)  

---
