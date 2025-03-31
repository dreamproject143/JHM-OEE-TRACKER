import os
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify
from openpyxl import load_workbook
from io import BytesIO
import gc

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB file size limit

# Create upload directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Memory cleanup middleware
@app.after_request
def cleanup(response):
    gc.collect()
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'files' not in request.files:
            return jsonify({'status': 'error', 'message': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'status': 'error', 'message': 'No files selected'}), 400

        uploaded_files = []
        for file in files:
            if file.filename == '':
                continue
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            uploaded_files.append(file.filename)

        gc.collect()
        return jsonify({
            'status': 'success',
            'message': f'{len(uploaded_files)} files uploaded successfully',
            'count': len(uploaded_files)
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_files():
    machine_data = {}
    
    try:
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            wb = load_workbook(filename=filepath, data_only=True)
            
            if "MANUAL LINE" not in wb.sheetnames:
                continue

            sheet = wb['MANUAL LINE']
            # Add your data processing logic here
            
            wb.close()  # Important: Close workbook

        # Add your data aggregation logic here
        summary_df = pd.DataFrame()  # Replace with actual dataframe

    except Exception as e:
        raise e
    finally:
        gc.collect()
    
    return summary_df

@app.route('/process', methods=['POST'])
def process_and_download():
    try:
        summary_df = process_files()
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            
            # Formatting
            workbook = writer.book
            worksheet = writer.sheets['Summary']
            header_format = workbook.add_format({
                'bold': True, 'bg_color': '#1F497D', 
                'font_color': 'white', 'border': 1
            })
            worksheet.set_row(0, None, header_format)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name='OEE_Report.xlsx',
            as_attachment=True
        )
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        gc.collect()

if __name__ == '__main__':
    app.run(debug=False)
