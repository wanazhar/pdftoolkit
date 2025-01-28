from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello World"

from flask import Flask, request, send_file, render_template
from pikepdf import Pdf, Encryption
import io
import zipfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    password = request.form.get('password')
    files = request.files.getlist('pdfs')

    if not password or not files:
        return "Password and files are required", 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            if file.filename.lower().endswith('.pdf'):
                try:
                    file_data = file.read()
                    with io.BytesIO(file_data) as pdf_stream:
                        pdf = Pdf.open(pdf_stream)
                        encrypted_pdf = io.BytesIO()
                        encryption = Encryption(owner=password, user=password)
                        pdf.save(encrypted_pdf, encryption=encryption)
                        encrypted_pdf.seek(0)
                        zip_file.writestr(f"encrypted_{file.filename}", encrypted_pdf.read())
                except Exception as e:
                    return f"Error processing {file.filename}: {str(e)}", 500

    zip_buffer.seek(0)
    return send_file(zip_buffer, as_attachment=True, download_name='encrypted_pdfs.zip')

if __name__ == '__main__':
    app.run(debug=True)
