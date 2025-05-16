from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash
import os
import zipfile
import uuid
import shutil
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Folder Paths
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'extracted'
CONVERT_FOLDER = 'converted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)
os.makedirs(CONVERT_FOLDER, exist_ok=True)

# Home Page Route
@app.route('/')
def index():
    return render_template('index.html')

# File Upload and Extraction Route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    files = request.files.getlist('file')
    extract_id = str(uuid.uuid4())
    extract_path = os.path.join(EXTRACT_FOLDER, extract_id)
    os.makedirs(extract_path, exist_ok=True)
    file_info = []

    for file in files:
        if file.filename == '':
            continue
        zip_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(zip_path)
        
        # Attempt to extract the file
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract all files, preserving the folder structure
                for member in zip_ref.namelist():
                    # Extract the file to the specified folder
                    try:
                        zip_ref.extract(member, extract_path)
                        extracted_file_path = os.path.join(extract_path, member)
                        if os.path.isfile(extracted_file_path):
                            file_size = os.path.getsize(extracted_file_path)
                            file_info.append((member, file_size))
                    except Exception as e:
                        flash(f'Error extracting {member}: {str(e)}', 'error')
        except zipfile.BadZipFile:
            flash(f'Failed to extract {file.filename}', 'error')
            continue

    if file_info:
        flash('Extraction completed successfully!', 'success')
        return redirect(url_for('show_files', extract_id=extract_id))
    else:
        flash('No valid ZIP files were extracted.', 'error')
        return redirect(url_for('index'))

# Display Extracted Files Route
@app.route('/files/<extract_id>')
def show_files(extract_id):
    extract_path = os.path.join(EXTRACT_FOLDER, extract_id)
    if not os.path.exists(extract_path):
        return "Files not found", 404

    # Recursively list all files including subdirectories
    file_list = []
    for root, _, files in os.walk(extract_path):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), extract_path)
            file_size = os.path.getsize(os.path.join(root, file))
            file_list.append((relative_path, file_size))

    return render_template('files.html', extract_id=extract_id, file_list=file_list)

# Download Extracted File Route
@app.route('/download/<extract_id>/<path:filename>')
def download_file(extract_id, filename):
    extract_path = os.path.join(EXTRACT_FOLDER, extract_id)
    return send_from_directory(extract_path, filename, as_attachment=True)

# File Conversion (TXT to PDF) Route
@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    # Save the uploaded TXT file
    txt_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(txt_path)

    # Convert TXT to PDF
    pdf_filename = f"{os.path.splitext(file.filename)[0]}.pdf"
    pdf_path = os.path.join(CONVERT_FOLDER, pdf_filename)
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', size=12)
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                pdf.cell(0, 10, line.strip(), ln=True)
        pdf.output(pdf_path)
        flash('File converted to PDF successfully!', 'success')
        return send_from_directory(CONVERT_FOLDER, pdf_filename, as_attachment=True)
    except Exception as e:
        flash(f'Failed to convert file: {str(e)}', 'error')
        return redirect(url_for('index'))

# Clean Up Old Files Route
@app.route('/cleanup')
def cleanup():
    try:
        shutil.rmtree(UPLOAD_FOLDER)
        shutil.rmtree(EXTRACT_FOLDER)
        shutil.rmtree(CONVERT_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(EXTRACT_FOLDER, exist_ok=True)
        os.makedirs(CONVERT_FOLDER, exist_ok=True)
        flash('All files cleaned up successfully!', 'success')
    except Exception as e:
        flash(f'Error during cleanup: {str(e)}', 'error')
    return redirect(url_for('index'))

# Run the Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
