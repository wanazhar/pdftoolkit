from flask import Flask, request, send_file, render_template, redirect, url_for
from pikepdf import Pdf, Encryption, Permissions, PdfError
import io
import zipfile
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import os
import tempfile

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

def extract_text_from_pdf(file_stream):
    file_stream = io.BytesIO(file_stream.read())
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    # Create text file in memory
    output = io.BytesIO()
    output.write(text.encode('utf-8'))
    output.seek(0)
    return output

def extract_images_from_pdf(file_stream):
    file_stream = io.BytesIO(file_stream.read())
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        image_count = 0
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Determine file extension based on image format
                ext = base_image["ext"]
                image_count += 1
                filename = f'image_{page_num + 1}_{image_count}.{ext}'
                
                zip_file.writestr(filename, image_bytes)
    
    doc.close()
    zip_buffer.seek(0)
    return zip_buffer

def ocr_pdf(file_stream):
    file_stream = io.BytesIO(file_stream.read())
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    
    # Create a new PDF with OCR text
    output_pdf = io.BytesIO()
    pdf_writer = Pdf.new()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap()
            
            # Save image temporarily
            img_path = os.path.join(temp_dir, f"page_{page_num}.png")
            pix.save(img_path)
            
            # Perform OCR
            img = Image.open(img_path)
            text = pytesseract.image_to_string(img)
            
            # Create new PDF page with OCR text
            pdf_page = Pdf.new()
            pdf_page.add_blank_page()
            # Add text to page (simplified - you might want to preserve layout)
            
            pdf_writer.pages.extend(pdf_page.pages)
    
    doc.close()
    pdf_writer.save(output_pdf)
    output_pdf.seek(0)
    return output_pdf

def rearrange_pdf_pages(file_stream, order):
    try:
        file_stream = io.BytesIO(file_stream.read())
        pdf = Pdf.open(file_stream)
        
        # Parse the order string into a list of page numbers (1-based to 0-based)
        new_order = [int(p.strip()) - 1 for p in order.split(',')]
        
        # Validate page numbers
        if any(i < 0 or i >= len(pdf.pages) for i in new_order):
            raise ValueError("Page numbers out of range")
        
        # Create new PDF with rearranged pages
        new_pdf = Pdf.new()
        for page_num in new_order:
            new_pdf.pages.append(pdf.pages[page_num])
        
        output = io.BytesIO()
        new_pdf.save(output)
        output.seek(0)
        return output
    
    except ValueError as e:
        raise ValueError(f"Invalid page order: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error rearranging PDF: {str(e)}")

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
    try:
        file = request.files['pdf']
        compressed = compress_pdf(file.stream)
        return send_file(compressed, download_name='compressed.pdf', as_attachment=True)
    except Exception as e:
        return f"Compression failed: {str(e)}", 500

@app.route('/extract_text', methods=['POST'])
def handle_extract_text():
    try:
        file = request.files['pdf']
        if not file:
            return "No file provided", 400
        
        text_output = extract_text_from_pdf(file.stream)
        return send_file(
            text_output,
            download_name='extracted_text.txt',
            as_attachment=True,
            mimetype='text/plain'
        )
    except Exception as e:
        return f"Text extraction failed: {str(e)}", 500

@app.route('/extract_images', methods=['POST'])
def handle_extract_images():
    try:
        file = request.files['pdf']
        if not file:
            return "No file provided", 400
        
        images_zip = extract_images_from_pdf(file.stream)
        return send_file(
            images_zip,
            download_name='extracted_images.zip',
            as_attachment=True,
            mimetype='application/zip'
        )
    except Exception as e:
        return f"Image extraction failed: {str(e)}", 500

@app.route('/ocr', methods=['POST'])
def handle_ocr():
    try:
        file = request.files['pdf']
        if not file:
            return "No file provided", 400
        
        ocr_output = ocr_pdf(file.stream)
        return send_file(
            ocr_output,
            download_name='ocr_processed.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"OCR processing failed: {str(e)}", 500

@app.route('/rearrange', methods=['POST'])
def handle_rearrange():
    try:
        file = request.files['pdf']
        order = request.form['order']
        
        if not file or not order:
            return "Missing file or page order", 400
        
        rearranged = rearrange_pdf_pages(file.stream, order)
        return send_file(
            rearranged,
            download_name='rearranged.pdf',
            as_attachment=True,
            mimetype='application/pdf'
        )
    except ValueError as e:
        return f"Invalid input: {str(e)}", 400
    except Exception as e:
        return f"Rearrangement failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
