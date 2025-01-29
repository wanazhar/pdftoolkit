from flask import Flask, request, send_file, render_template, redirect, url_for
from pikepdf import Pdf, Encryption, Permissions, PdfError
import io
import zipfile
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# ======== PDF Operations ========
def encrypt_pdf(file_stream, password):
    pdf = Pdf.open(file_stream)
    encryption = Encryption(owner=password, user=password, allow=Permissions(extract=True))
    output = io.BytesIO()
    pdf.save(output, encryption=encryption)
    output.seek(0)
    return output

def merge_pdfs(files):
    merged = Pdf.new()
    for file in files:
        src = Pdf.open(io.BytesIO(file.read()))
        merged.pages.extend(src.pages)
    output = io.BytesIO()
    merged.save(output)
    output.seek(0)
    return output

def split_pdf(file_stream, ranges):
    src = Pdf.open(file_stream)
    output = io.BytesIO()
    split = Pdf.new()

    for r in ranges.split(','):
        if '-' in r:
            start, end = map(int, r.split('-'))
            split.pages.extend(src.pages[start-1:end])
        else:
            split.pages.append(src.pages[int(r)-1])

    split.save(output)
    output.seek(0)
    return output

def compress_pdf(file_stream):
    pdf = Pdf.open(file_stream)

    # Simple compression by removing duplicate objects
    pdf.remove_unreferenced_resources()

    output = io.BytesIO()
    pdf.save(output, compress_streams=True, object_stream_mode=2)
    output.seek(0)
    return output

# ======== Routes ========
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/encrypt', methods=['POST'])
def handle_encrypt():
    try:
        password = request.form['password']
        files = request.files.getlist('pdfs')

        if not files or not password:
            return redirect(url_for('home'))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                if file.filename.lower().endswith('.pdf'):
                    encrypted = encrypt_pdf(file.stream, password)
                    zip_file.writestr(f"encrypted_{file.filename}", encrypted.read())

        zip_buffer.seek(0)
        return send_file(zip_buffer, download_name='encrypted_files.zip', as_attachment=True)

    except PdfError as e:
        return f"PDF Error: {str(e)}", 400
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500

@app.route('/merge', methods=['POST'])  # ✅ Properly indented after previous function
def handle_merge():
    try:
        files = request.files.getlist('pdfs')
        if len(files) < 2:
            return "Please upload at least 2 PDF files to merge", 400

        merged = merge_pdfs(files)
        return send_file(merged, download_name='merged.pdf', as_attachment=True)

    except PdfError as e:
        return f"Merge failed: {str(e)}", 400
    except Exception as e:
        return f"Merge error: {str(e)}", 500

@app.route('/split', methods=['POST'])
def handle_split():
    file = request.files['pdf']
    ranges = request.form['pages']
    split = split_pdf(file.stream, ranges)
    return send_file(split, download_name='split.pdf', as_attachment=True)

@app.route('/compress', methods=['POST'])
def handle_compress():
    file = request.files['pdf']
    compressed = compress_pdf(file.stream)
    return send_file(compressed, download_name='compressed.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
