from flask import Flask, request, render_template, jsonify, send_file
import os
import pandas as pd
from openpyxl import load_workbook
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Create upload and output folders
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    return jsonify({"message": "File uploaded successfully", "filename": filename})

@app.route('/process', methods=['POST'])
def process_file():
    filename = request.json.get("filename")
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    try:
        wb = load_workbook(filename=filepath, data_only=True)
        if "MANUAL LINE" not in wb.sheetnames:
            return jsonify({"error": "Sheet 'MANUAL LINE' not found"}), 400

        sheet = wb['MANUAL LINE']

        machine_data = {}
        for row in sheet.iter_rows(min_row=2, values_only=True):
            machine = str(row[0]).strip() if row[0] else ""
            gross_value = row[1]

            if machine and gross_value:
                percentage = float(gross_value) / 100
                if machine not in machine_data:
                    machine_data[machine] = []
                machine_data[machine].append(percentage)

        # Calculate averages
        summary_data = {machine: sum(values) / len(values) for machine, values in machine_data.items()}

        # Save to Excel
        output_file = os.path.join(OUTPUT_FOLDER, "Machine_Performance_Summary.xlsx")
        df = pd.DataFrame(list(summary_data.items()), columns=["Work Center", "Performance"])
        df.to_excel(output_file, index=False)

        return jsonify({"message": "Processing complete", "output_file": "Machine_Performance_Summary.xlsx"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_file():
    output_file = os.path.join(OUTPUT_FOLDER, "Machine_Performance_Summary.xlsx")
    if os.path.exists(output_file):
        return send_file(output_file, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
