# app.py
import os
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify
from openpyxl import load_workbook
from io import BytesIO

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'message': 'No files uploaded', 'status': 'error'}), 400
    
    files = request.files.getlist('files')
    if len(files) == 0 or all(file.filename == '' for file in files):
        return jsonify({'message': 'No selected files', 'status': 'error'}), 400

    try:
        for file in files:
            if file.filename == '':
                continue
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return jsonify({
            'message': f'{len(files)} files uploaded successfully!',
            'status': 'success',
            'count': len(files)
        })
    except Exception as e:
        return jsonify({'message': f'Upload failed: {str(e)}', 'status': 'error'}), 500

def process_files():
    machine_data = {}
    
    for file_name in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        try:
            wb = load_workbook(filename=file_path, data_only=True)
            if "MANUAL LINE" not in wb.sheetnames:
                continue

            sheet = wb['MANUAL LINE']
            # ... [rest of your original processing logic] ...
            # (Keep the same processing code but ensure all paths are properly closed)

        except Exception as e:
            print(f"Error processing {file_name}: {str(e)}")
            continue

    # ... [rest of your original data processing] ...

    return summary_df

@app.route('/process', methods=['POST'])
def process_and_download():
    try:
        summary_df = process_files()
        
        # Create in-memory file with proper Excel handling
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            summary_df.to_excel(writer, sheet_name="Summary", na_rep='')
            
            # Formatting code here...
            workbook = writer.book
            worksheet = writer.sheets['Summary']
            # ... [your formatting code] ...

        # Reset buffer position and send
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name='Machine_Performance_Summary.xlsx',
            as_attachment=True
        )
        
    except Exception as e:
        app.logger.error(f'Processing error: {str(e)}')
        return jsonify({'message': f'Error: {str(e)}', 'status': 'error'}), 500

if __name__ == '__main__':
    app.run(debug=False)
