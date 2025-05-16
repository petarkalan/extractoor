from flask import Flask, request, send_from_directory, render_template, redirect, url_for, flash
import os
import zipfile
import uuid
import shutil
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
EXTRACT_FOLDER = 'extracted'
CONVERT_FOLDER = 'converted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)
os.makedirs(CONVERT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

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
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
                for name in zip_ref.namelist():
                    file_size = os.path.getsize(os.path.join(extract_path, name))
                    file_info.append((name, file_size))
        except zipfile.BadZipFile:
            flash(f'Failed to extract {file.filename}', 'error')
            continue

    flash('Extraction completed successfully!', 'success')
    return redirect(url_for('show_files', extract_id=extract_id))

@app.route('/files/<extract_id>')
def show_files(extract_id):
    extract_path = os.path.join(EXTRACT_FOLDER, extract_id)
    if not os.path.exists(extract_path):
        return "Files not found", 404
    file_list = [(f, os.path.getsize(os.path.join(extract_path, f))) for f in os.listdir(extract_path)]
    return render_template('files.html', extract_id=extract_id, file_list=file_list)

@app.route('/download/<extract_id>/<filename>')
def download_file(extract_id, filename):
    extract_path = os.path.join(EXTRACT_FOLDER, extract_id)
    return send_from_directory(extract_path, filename, as_attachment=True)

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))

    # Save the uploaded file
    txt_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(txt_path)

    # Convert TXT to PDF
    pdf_path = os.path.join(CONVERT_FOLDER, f"{os.path.splitext(file.filename)[0]}.pdf")
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', size=12)
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                pdf.cell(0, 10, line.strip(), ln=True)
        pdf.output(pdf_path)
        flash('File converted to PDF successfully!', 'success')
        return send_from_directory(CONVERT_FOLDER, f"{os.path.splitext(file.filename)[0]}.pdf", as_attachment=True)
    except Exception as e:
        flash(f'Failed to convert file: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)