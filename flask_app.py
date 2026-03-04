from flask import Flask, request, send_file, render_template, redirect, url_for
from pikepdf import Pdf, Encryption, Permissions, PdfError
import io
import zipfile
import pytesseract
from pytesseract import TesseractNotFoundError
from PIL import Image
import fitz  # PyMuPDF
import os
import tempfile

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100MB


def _read_all_bytes(file_stream) -> bytes:
    """
    Read the uploaded file stream exactly once and return raw bytes.
    This avoids empty reads when the stream cursor is already at EOF.
    """
    data = file_stream.read()
    if not data:
        raise ValueError("Empty upload or unreadable file stream")
    return data


# ======== PDF Operations ========
def encrypt_pdf(file_stream, password):
    file_bytes = _read_all_bytes(file_stream)
    pdf = Pdf.open(io.BytesIO(file_bytes))
    encryption = Encryption(owner=password, user=password, allow=Permissions(extract=True))
    output = io.BytesIO()
    pdf.save(output, encryption=encryption)
    output.seek(0)
    return output


def decrypt_pdf(file_stream, password):
    try:
        file_bytes = _read_all_bytes(file_stream)
        pdf = Pdf.open(io.BytesIO(file_bytes), password=password)
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
    """
    Returns (buffer, download_name, mimetype)
    download_name is either split.pdf or split_files.zip
    """
    try:
        file_bytes = _read_all_bytes(file_stream)
        src = Pdf.open(io.BytesIO(file_bytes))
        num_pages = len(src.pages)

        output_files = []
        output_zip = io.BytesIO()

        if ranges.lower().startswith("every"):
            try:
                interval = int(ranges.split()[1])
                if interval < 1:
                    raise ValueError("Invalid interval size.")

                for i in range(0, num_pages, interval):
                    split_doc = Pdf.new()
                    split_doc.pages.extend(src.pages[i : i + interval])

                    pdf_output = io.BytesIO()
                    split_doc.save(pdf_output)
                    pdf_output.seek(0)
                    output_files.append((f"split_{i+1}-{min(i+interval, num_pages)}.pdf", pdf_output))
            except (IndexError, ValueError):
                raise ValueError("Invalid format. Use 'every X pages', for example: 'every 2 pages'.")

        else:
            for r in ranges.split(","):
                r = r.strip()
                split_doc = Pdf.new()

                if "-" in r:
                    try:
                        start, end = map(int, r.split("-"))
                        if start < 1 or end > num_pages or start > end:
                            raise ValueError(f"Invalid range: {r}")
                        split_doc.pages.extend(src.pages[start - 1 : end])
                    except ValueError:
                        raise ValueError(f"Invalid range format: {r}")
                else:
                    try:
                        page_num = int(r)
                        if page_num < 1 or page_num > num_pages:
                            raise ValueError(f"Page number out of range: {r}")
                        split_doc.pages.append(src.pages[page_num - 1])
                    except ValueError:
                        raise ValueError(f"Invalid page number: {r}")

                if split_doc.pages:
                    pdf_output = io.BytesIO()
                    split_doc.save(pdf_output)
                    pdf_output.seek(0)
                    output_files.append((f"split_{r}.pdf", pdf_output))

        if len(output_files) > 1:
            with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for filename, pdf_output in output_files:
                    zip_file.writestr(filename, pdf_output.read())
            output_zip.seek(0)
            return output_zip, "split_files.zip", "application/zip"

        if not output_files:
            raise ValueError("No pages matched the requested ranges")

        single_buf = output_files[0][1]
        single_buf.seek(0)
        return single_buf, "split.pdf", "application/pdf"

    except PdfError as e:
        raise PdfError(f"PDF Processing Error: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")


def compress_pdf(file_stream):
    file_bytes = _read_all_bytes(file_stream)
    pdf = Pdf.open(io.BytesIO(file_bytes))
    pdf.remove_unreferenced_resources()
    output = io.BytesIO()
    pdf.save(output, compress_streams=True, object_stream_mode=2)
    output.seek(0)
    return output


def extract_text_from_pdf(file_stream):
    file_bytes = _read_all_bytes(file_stream)
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_chunks = []
    for page in doc:
        text_chunks.append(page.get_text())
    doc.close()

    output = io.BytesIO()
    output.write(("".join(text_chunks)).encode("utf-8"))
    output.seek(0)
    return output


def extract_images_from_pdf(file_stream):
    file_bytes = _read_all_bytes(file_stream)
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        image_count = 0
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)

            for img in image_list:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image.get("ext", "bin")

                image_count += 1
                filename = f"image_{page_num + 1}_{image_count}.{ext}"
                zip_file.writestr(filename, image_bytes)

        if image_count == 0:
            zip_file.writestr("README.txt", "No embedded images were found in this PDF.\n")

    doc.close()
    zip_buffer.seek(0)
    return zip_buffer


def _ensure_tesseract_available():
    try:
        _ = pytesseract.get_tesseract_version()
    except TesseractNotFoundError as e:
        raise RuntimeError(
            "Tesseract is not available on the server, so OCR cannot run. "
            "On PythonAnywhere free plan, system packages like tesseract are usually not installable. "
            "Either disable the OCR feature, upgrade your plan, or use an external OCR API."
        ) from e


def ocr_pdf(file_stream):
    _ensure_tesseract_available()

    file_bytes = _read_all_bytes(file_stream)
    src = fitz.open(stream=file_bytes, filetype="pdf")

    out = fitz.open()

    with tempfile.TemporaryDirectory() as temp_dir:
        for page_num in range(len(src)):
            page = src[page_num]
            pix = page.get_pixmap()

            img_path = os.path.join(temp_dir, f"page_{page_num}.png")
            pix.save(img_path)

            img = Image.open(img_path)
            text = pytesseract.image_to_string(img)

            rect = page.rect
            out_page = out.new_page(width=rect.width, height=rect.height)

            out_page.insert_image(rect, filename=img_path)

            safe_text = (text or "").strip()
            if safe_text:
                out_page.insert_text((20, 20), safe_text[:20000], fontsize=9)

    src.close()

    output_pdf = io.BytesIO()
    out.save(output_pdf)
    out.close()
    output_pdf.seek(0)
    return output_pdf


def rearrange_pdf_pages(file_stream, order):
    try:
        file_bytes = _read_all_bytes(file_stream)
        pdf = Pdf.open(io.BytesIO(file_bytes))

        new_order = [int(p.strip()) - 1 for p in order.split(",") if p.strip()]

        if not new_order:
            raise ValueError("No page numbers provided")

        if any(i < 0 or i >= len(pdf.pages) for i in new_order):
            raise ValueError("Page numbers out of range")

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


def rotate_pdf(file_stream, degree):
    try:
        file_bytes = _read_all_bytes(file_stream)
        pdf = Pdf.open(io.BytesIO(file_bytes))
        for page in pdf.pages:
            page.rotate(degree, relative=True)
        output = io.BytesIO()
        pdf.save(output)
        output.seek(0)
        return output
    except Exception as e:
        raise RuntimeError(f"Rotation failed: {str(e)}")


def pdf_to_images(file_stream):
    try:
        file_bytes = _read_all_bytes(file_stream)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap()
                img_bytes = pix.tobytes("png")
                zip_file.writestr(f"page_{page_num + 1}.png", img_bytes)
        doc.close()
        zip_buffer.seek(0)
        return zip_buffer
    except Exception as e:
        raise RuntimeError(f"Conversion failed: {str(e)}")


def images_to_pdf(image_files):
    try:
        doc = fitz.open()
        for img_file in image_files:
            img_bytes = img_file.read()
            img = fitz.open(stream=img_bytes, filetype=img_file.filename.split('.')[-1])
            rect = img[0].rect
            pdfbytes = img.convert_to_pdf()
            img.close()
            img_pdf = fitz.open("pdf", pdfbytes)
            page = doc.new_page(width=rect.width, height=rect.height)
            page.show_pdf_page(rect, img_pdf, 0)
            img_pdf.close()
        output = io.BytesIO()
        doc.save(output)
        doc.close()
        output.seek(0)
        return output
    except Exception as e:
        raise RuntimeError(f"Conversion failed: {str(e)}")


def add_watermark(file_stream, watermark_text):
    try:
        file_bytes = _read_all_bytes(file_stream)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            # Add watermark text diagonally
            page.insert_text(
                (50, 50),
                watermark_text,
                fontsize=50,
                color=(0.8, 0.8, 0.8),
                fill_opacity=0.3,
                rotate=45
            )
        output = io.BytesIO()
        doc.save(output)
        doc.close()
        output.seek(0)
        return output
    except Exception as e:
        raise RuntimeError(f"Watermarking failed: {str(e)}")


# ======== Routes ========
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/encrypt", methods=["POST"])
def handle_encrypt():
    try:
        password = request.form.get("password")
        files = request.files.getlist("pdfs")

        if not files or not any(f.filename for f in files):
            return "No files uploaded", 400
        if not password:
            return "Password is required", 400

        zip_buffer = io.BytesIO()
        pdf_count = 0
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                if not file.filename:
                    continue
                if file.filename.lower().endswith(".pdf"):
                    encrypted = encrypt_pdf(file.stream, password)
                    zip_file.writestr(f"encrypted_{file.filename}", encrypted.read())
                    pdf_count += 1
                else:
                    return f"Invalid file type: {file.filename}. Only PDFs are allowed.", 400

        if pdf_count == 0:
            return "No valid PDF files found", 400

        zip_buffer.seek(0)
        return send_file(zip_buffer, download_name="encrypted_files.zip", as_attachment=True)

    except PdfError as e:
        return f"PDF Error: {str(e)}", 400
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500


@app.route("/decrypt", methods=["POST"])
def handle_decrypt():
    try:
        password = request.form.get("password")
        files = request.files.getlist("pdfs")

        if not files or not any(f.filename for f in files):
            return "No files uploaded", 400
        if not password:
            return "Password is required", 400

        zip_buffer = io.BytesIO()
        pdf_count = 0
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in files:
                if not file.filename:
                    continue
                if file.filename.lower().endswith(".pdf"):
                    try:
                        decrypted = decrypt_pdf(file.stream, password)
                        zip_file.writestr(f"decrypted_{file.filename}", decrypted.read())
                        pdf_count += 1
                    except PdfError as e:
                        zip_file.writestr(f"error_{file.filename}.txt", str(e))
                else:
                    return f"Invalid file type: {file.filename}. Only PDFs are allowed.", 400

        if pdf_count == 0:
            return "No valid PDF files found", 400

        zip_buffer.seek(0)
        return send_file(zip_buffer, download_name="decrypted_files.zip", as_attachment=True)

    except PdfError as e:
        return f"Decryption failed: {str(e)}", 400
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500


@app.route("/merge", methods=["POST"])
def handle_merge():
    try:
        files = request.files.getlist("pdfs")
        if not files or not any(f.filename for f in files):
            return "No files uploaded", 400

        valid_files = [f for f in files if f.filename and f.filename.lower().endswith(".pdf")]
        if len(valid_files) < 2:
            return "Please upload at least 2 PDF files to merge", 400

        merged = merge_pdfs(valid_files)
        return send_file(merged, download_name="merged.pdf", as_attachment=True)

    except PdfError as e:
        return f"Merge failed: {str(e)}", 400
    except Exception as e:
        return f"Merge error: {str(e)}", 500


@app.route("/split", methods=["POST"])
def handle_split():
    try:
        file = request.files.get("pdf")
        ranges = request.form.get("pages")

        if not file or not file.filename:
            return "No file uploaded", 400
        if not file.filename.lower().endswith(".pdf"):
            return "Invalid file type. Only PDFs are allowed.", 400
        if not ranges:
            return "Missing page ranges", 400

        buf, download_name, mimetype = split_pdf(file.stream, ranges)
        return send_file(buf, download_name=download_name, as_attachment=True, mimetype=mimetype)

    except ValueError as e:
        return f"Invalid input: {str(e)}", 400
    except PdfError as e:
        return f"PDF Error: {str(e)}", 400
    except Exception as e:
        return f"Unexpected error: {str(e)}", 500


@app.route("/compress", methods=["POST"])
def handle_compress():
    try:
        file = request.files.get("pdf")
        if not file or not file.filename:
            return "No file uploaded", 400
        if not file.filename.lower().endswith(".pdf"):
            return "Invalid file type. Only PDFs are allowed.", 400

        compressed = compress_pdf(file.stream)
        return send_file(compressed, download_name="compressed.pdf", as_attachment=True)
    except Exception as e:
        return f"Compression failed: {str(e)}", 500


@app.route("/extract_text", methods=["POST"])
def handle_extract_text():
    try:
        file = request.files.get("pdf")
        if not file or not file.filename:
            return "No file uploaded", 400
        if not file.filename.lower().endswith(".pdf"):
            return "Invalid file type. Only PDFs are allowed.", 400

        text_output = extract_text_from_pdf(file.stream)
        return send_file(
            text_output,
            download_name="extracted_text.txt",
            as_attachment=True,
            mimetype="text/plain",
        )
    except Exception as e:
        return f"Text extraction failed: {str(e)}", 500


@app.route("/extract_images", methods=["POST"])
def handle_extract_images():
    try:
        file = request.files.get("pdf")
        if not file or not file.filename:
            return "No file uploaded", 400
        if not file.filename.lower().endswith(".pdf"):
            return "Invalid file type. Only PDFs are allowed.", 400

        images_zip = extract_images_from_pdf(file.stream)
        return send_file(
            images_zip,
            download_name="extracted_images.zip",
            as_attachment=True,
            mimetype="application/zip",
        )
    except Exception as e:
        return f"Image extraction failed: {str(e)}", 500


@app.route("/ocr", methods=["POST"])
def handle_ocr():
    try:
        file = request.files.get("pdf")
        if not file or not file.filename:
            return "No file uploaded", 400
        if not file.filename.lower().endswith(".pdf"):
            return "Invalid file type. Only PDFs are allowed.", 400

        ocr_output = ocr_pdf(file.stream)
        return send_file(
            ocr_output,
            download_name="ocr_processed.pdf",
            as_attachment=True,
            mimetype="application/pdf",
        )
    except Exception as e:
        return f"OCR processing failed: {str(e)}", 500


@app.route("/rearrange", methods=["POST"])
def handle_rearrange():
    try:
        file = request.files.get("pdf")
        order = request.form.get("order")

        if not file or not file.filename:
            return "No file uploaded", 400
        if not file.filename.lower().endswith(".pdf"):
            return "Invalid file type. Only PDFs are allowed.", 400
        if not order:
            return "Missing page order", 400

        rearranged = rearrange_pdf_pages(file.stream, order)
        return send_file(rearranged, download_name="rearranged.pdf", as_attachment=True, mimetype="application/pdf")

    except ValueError as e:
        return f"Invalid input: {str(e)}", 400
    except Exception as e:
        return f"Rearrangement failed: {str(e)}", 500


@app.route("/rotate", methods=["POST"])
def handle_rotate():
    try:
        file = request.files.get("pdf")
        degree = request.form.get("degree", type=int)
        if not file or not file.filename:
            return "No file uploaded", 400
        if not degree:
            return "Rotation degree required", 400
        rotated = rotate_pdf(file.stream, degree)
        return send_file(rotated, download_name="rotated.pdf", as_attachment=True)
    except Exception as e:
        return f"Rotation failed: {str(e)}", 500


@app.route("/pdf_to_images", methods=["POST"])
def handle_pdf_to_images():
    try:
        file = request.files.get("pdf")
        if not file or not file.filename:
            return "No file uploaded", 400
        images_zip = pdf_to_images(file.stream)
        return send_file(images_zip, download_name="pdf_images.zip", as_attachment=True)
    except Exception as e:
        return f"Conversion failed: {str(e)}", 500


@app.route("/images_to_pdf", methods=["POST"])
def handle_images_to_pdf():
    try:
        files = request.files.getlist("images")
        if not files or not any(f.filename for f in files):
            return "No images uploaded", 400
        pdf_output = images_to_pdf(files)
        return send_file(pdf_output, download_name="images_to.pdf", as_attachment=True)
    except Exception as e:
        return f"Conversion failed: {str(e)}", 500


@app.route("/watermark", methods=["POST"])
def handle_watermark():
    try:
        file = request.files.get("pdf")
        text = request.form.get("text")
        if not file or not file.filename:
            return "No file uploaded", 400
        if not text:
            return "Watermark text required", 400
        watermarked = add_watermark(file.stream, text)
        return send_file(watermarked, download_name="watermarked.pdf", as_attachment=True)
    except Exception as e:
        return f"Watermarking failed: {str(e)}", 500


if __name__ == "__main__":
    app.run(debug=True)
