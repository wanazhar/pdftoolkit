from flask import Flask, request, send_file, render_template, redirect, url_for
from pikepdf import Pdf, Encryption, Permissions, PdfError
import io
import zipfile

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# ======== PDF Operations ========
def encrypt_pdf(file_stream, password):
    file_stream = io.BytesIO(file_stream.read())  # Convert to BytesIO
    pdf = Pdf.open(file_stream)
    encryption = Encryption(owner=password, user=password, allow=Permissions(extract=True))
    output = io.BytesIO()
    pdf.save(output, encryption=encryption)
    output.seek(0)
    return output

def decrypt_pdf(file_stream, password):
    try:
        file_stream = io.BytesIO(file_stream.read())  # Convert to BytesIO
        pdf = Pdf.open(file_stream, password=password)
        output = io.BytesIO()
        pdf.save(output)
        output.seek(0)
        return output
    except PdfError:
        raise PdfError("Incorrect password or invalid PDF.")

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
    try:
        file_stream = io.BytesIO(file_stream.read())  # Ensure it's a BytesIO object
        src = Pdf.open(file_stream)
        num_pages = len(src.pages)

        output_files = []
        output_zip = io.BytesIO()

        # Handle "every X pages" logic
        if ranges.lower().startswith("every"):
            try:
                interval = int(ranges.split()[1])  # Extract the number after "every"
                if interval < 1:
                    raise ValueError("Invalid interval size.")

                for i in range(0, num_pages, interval):
                    split = Pdf.new()
                    split.pages.extend(src.pages[i:i+interval])

                    pdf_output = io.BytesIO()
                    split.save(pdf_output)
                    pdf_output.seek(0)

                    output_files.append((f"split_{i+1}-{min(i+interval, num_pages)}.pdf", pdf_output))
            except (IndexError, ValueError):
                raise ValueError("Invalid format. Use 'every X pages', e.g., 'every 2 pages'.")

        else:
            # Process custom ranges like "1-2,3-4"
            for r in ranges.split(','):
                r = r.strip()
                split = Pdf.new()

                if '-' in r:
                    try:
                        start, end = map(int, r.split('-'))
                        if start < 1 or end > num_pages or start > end:
                            raise ValueError(f"Invalid range: {r}")
                        split.pages.extend(src.pages[start - 1:end])
                    except ValueError:
                        raise ValueError(f"Invalid range format: {r}")
                else:
                    try:
                        page_num = int(r)
                        if page_num < 1 or page_num > num_pages:
                            raise ValueError(f"Page number out of range: {r}")
                        split.pages.append(src.pages[page_num - 1])
                    except ValueError:
                        raise ValueError(f"Invalid page number: {r}")

                if split.pages:
                    pdf_output = io.BytesIO()
                    split.save(pdf_output)
                    pdf_output.seek(0)
                    output_files.append((f"split_{r}.pdf", pdf_output))

        # Create ZIP if multiple files exist
        if len(output_files) > 1:
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, pdf_output in output_files:
                    zip_file.writestr(filename, pdf_output.read())

            output_zip.seek(0)
            return output_zip
        else:
            return output_files[0][1]  # Single PDF output

    except PdfError as e:
        raise PdfError(f"PDF Processing Error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")

def compress_pdf(file_stream):
    pdf = Pdf.open(file_stream)
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

@app.route('/decrypt', methods=['POST'])
def handle_decrypt():
    try:
        password = request.form['password']
        files = request.files.getlist('pdfs')

        if not files or not password:
            return redirect(url_for('home'))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                if file.filename.lower().endswith('.pdf'):
                    try:
                        decrypted = decrypt_pdf(file.stream, password)
                        zip_file.writestr(f"decrypted_{file.filename}", decrypted.read())
                    except PdfError as e:
                        zip_file.writestr(f"error_{file.filename}.txt", str(e))

        zip_buffer.seek(0)
        return send_file(zip_buffer, download_name='decrypted_files.zip', as_attachment=True)

    except PdfError as e:
        return f"Decryption failed: {str(e)}", 400
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500

@app.route('/merge', methods=['POST'])
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
    try:
        file = request.files.get('pdf')
        ranges = request.form.get('pages')

        if not file or not ranges:
            return "Missing file or page ranges", 400

        split_pdf_output = split_pdf(file.stream, ranges)
        
        if isinstance(split_pdf_output, io.BytesIO):  # If ZIP file
            return send_file(split_pdf_output, download_name='split_files.zip', as_attachment=True)
        else:  # If single file
            return send_file(split_pdf_output, download_name='split.pdf', as_attachment=True)

    except ValueError as e:
        return f"Invalid input: {str(e)}", 400
    except PdfError as e:
        return f"PDF Error: {str(e)}", 400
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500

@app.route('/compress', methods=['POST'])
def handle_compress():
    file = request.files['pdf']
    compressed = compress_pdf(file.stream)
    return send_file(compressed, download_name='compressed.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
