import os
import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify
from openpyxl import load_workbook
from io import BytesIO

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Error handlers for JSON responses
@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(405)
def handle_errors(e):
    return jsonify({
        'status': 'error',
        'message': str(e.description)
    }), e.code

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

        uploaded_count = 0
        for file in files:
            if file.filename == '':
                continue
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            uploaded_count += 1

        return jsonify({
            'status': 'success',
            'message': f'{uploaded_count} files uploaded successfully',
            'count': uploaded_count
        })

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_files():
    machine_data = {}
    
    for filename in os.listdir(UPLOAD_FOLDER):
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            wb = load_workbook(filename=filepath, data_only=True)
            if "MANUAL LINE" not in wb.sheetnames:
                continue

            sheet = wb['MANUAL LINE']
            # ... [keep your existing processing logic here] ...

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    # ... [keep your existing data processing logic here] ...

    return summary_df

@app.route('/process', methods=['POST'])
def process_and_download():
    try:
        summary_df = process_files()
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            summary_df.to_excel(writer, sheet_name="Summary", na_rep='')
            
            # Formatting
            workbook = writer.book
            worksheet = writer.sheets['Summary']
            header_format = workbook.add_format({
                'bold': True, 'font_size': 12, 
                'bg_color': '#1F497D', 'font_color': 'white',
                'border': 1, 'align': 'center'
            })
            cell_format = workbook.add_format({
                'border': 1, 'align': 'center', 
                'num_format': '0.00%', 'font_color': '#1F497D'
            })
            
            # Apply formatting
            worksheet.write_row(0, 0, ["Work Center"] + summary_df.columns.tolist(), header_format)
            for row_idx, (index, row) in enumerate(summary_df.iterrows(), 1):
                worksheet.write(row_idx, 0, index, cell_format)
                for col_idx, value in enumerate(row, 1):
                    worksheet.write(row_idx, col_idx, value, cell_format)
            
            # Set column widths
            worksheet.set_column(0, 0, 20)
            for idx in range(1, len(summary_df.columns)+1):
                worksheet.set_column(idx, idx, 15)

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name='Machine_Performance.xlsx',
            as_attachment=True
        )

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)
