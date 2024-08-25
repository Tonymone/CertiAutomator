import json
import os
import shutil
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pandas as pd
from fpdf import FPDF, XPos, YPos
import threading
import cv2
import time
from datetime import datetime

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)

# Configure paths and folders
UPLOAD_FOLDER = 'uploads'
GEN_FOLDER = 'gens'
CHECKPOINT_FILE = 'checkpoint.json'
TEMPLATE_PATH = 'certificate-template.png'
logo_path = 'university-of-mumbai logo.png'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GEN_FOLDER'] = GEN_FOLDER

# Ensure the upload and generation folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GEN_FOLDER, exist_ok=True)

# Status variable and lock for thread safety
status = {"message": ""}
status_lock = threading.Lock()

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"processed_seat_numbers": [], "step": "start"}

def save_checkpoint(seat_number, step):
    checkpoint = load_checkpoint()
    if seat_number != 0:
        checkpoint["processed_seat_numbers"].append(seat_number)
    checkpoint["step"] = step

    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(checkpoint, f)
    except Exception as e:
        print(f"Error writing checkpoint file: {e}")

def remove_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)

def load_excel_files(request):
    ms6_file = request.files['ms6File']
    bms_file = request.files['bmsFile']

    ms6_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'MS6.xlsx')
    bms_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'BMSOG.xlsx')

    ms6_file.save(ms6_file_path)
    bms_file.save(bms_file_path)

    try:
        df1 = pd.read_excel(ms6_file_path)
        df2 = pd.read_excel(bms_file_path)
    except Exception as e:
        print(f"Error reading Excel files: {e}")
        raise e

    return df1, df2, ms6_file_path, bms_file_path

def process_dataframes(df1, df2):
    pd.options.mode.copy_on_write = True

    # Drop duplicate COLL_NO from df1
    df1 = df1.drop_duplicates(subset=['COLL_NO'])
    
    df2['FREM'] = df2['FREM'].fillna('null')
    df2['RES'] = df2['RES'].fillna('null')

    dataT = df2[(df2['RSLT'] == 'P') & (df2['FREM'] == 'null') & (df2['RES'] == 'null')]
    dataT['Gender'] = dataT['SEX'].apply(lambda x: 'MALE' if x == 1 else 'FEMALE' if x == 2 else 'N/A')
    dataT = pd.merge(dataT, df1[['COLL_NO']], on='COLL_NO', how='left')
    dataT = dataT.sort_values(by='COLL_NO', ascending=True)
    dataT['pno'] = dataT.groupby('COLL_NO').cumcount() + 1
    dataT['COLL_NO'] = dataT['COLL_NO'].apply(lambda x: str(x).zfill(4))
    dataT['pno'] = dataT['pno'].apply(lambda x: str(x).zfill(4))

    return dataT

@app.route('/status', methods=['GET'])
def get_status():
    with status_lock:
        return jsonify(status)

@app.route('/delete-files', methods=['POST'])
def delete_files():
    try:
        delete_files_in_folder(app.config['GEN_FOLDER'])
        delete_files_in_folder(app.config['UPLOAD_FOLDER'])
        remove_checkpoint()
        return "Files deleted successfully", 200
    except Exception as e:
        print(f"Error deleting files: {e}")
        return "Error deleting files", 500

@app.route('/validate-files', methods=['POST'])
def validate_files():
    ms6_file = request.files.get('ms6File')
    bms_file = request.files.get('bmsFile')
    signature_file = request.files.get('signature')
    # logo_file = request.files.get('logo')

    if not ms6_file or not bms_file:
        return jsonify({'error': 'Both MS6 and BMS files are required.'}), 400

    if not signature_file:
        return jsonify({'error': 'Director`s signature is required.'}), 400

    required_columns_ms6 = ['COLL_NO']
    required_columns_bms = ['SEAT_NO', 'NAME', 'SEX', 'RSLT', 'FREM', 'RES']
    allowed_image_extensions = {'webp', 'png', 'jpg', 'jpeg'}

    try:
        # Validate file types
        if (ms6_file.filename.endswith(('.xlsx', '.xls')) and
            bms_file.filename.endswith(('.xlsx', '.xls')) and
            signature_file.filename.rsplit('.', 1)[1].lower() in allowed_image_extensions ):

            # Read and validate MS6 and BMS Excel files
            ms6_df = pd.read_excel(ms6_file)
            bms_df = pd.read_excel(bms_file)

            if not all(column in ms6_df.columns for column in required_columns_ms6):
                return jsonify({'error': 'MS6 file is missing required columns.'}), 400

            if not all(column in bms_df.columns for column in required_columns_bms):
                return jsonify({'error': 'BMS file is missing required columns.'}), 400

            return jsonify({'message': 'Files are valid!'}), 200

        else:
            return jsonify({'error': 'Invalid file types. Only .xlsx or .xls for MS6 and BMS files, and .webp .png, .jpg, or .jpeg for signature are allowed.'}), 400

    except Exception as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 500


@app.route('/generate-certificates', methods=['POST'])
def generate_certificates():
    global status

    checkpoint = load_checkpoint()
    processed_seat_numbers = checkpoint["processed_seat_numbers"]
    current_step = checkpoint["step"]

    if 'ms6File' not in request.files or 'bmsFile' not in request.files or 'year' not in request.form or 'selectedCourse' not in request.form:
        return "College file or course file not uploaded or year or course not selected", 400

    year = request.form['year']
    course_name = request.form['selectedCourse']
    # semester_number = request.form['semester']

    signature_file = request.files['signature']
    # logo_file = request.files['logo']

    with status_lock:
        status['message'] = "Processing request..."

    df1, df2, ms6_file_path, bms_file_path = load_excel_files(request)
    dataT = process_dataframes(df1, df2)

    output_pdf_path = os.path.abspath(os.path.join(app.config['GEN_FOLDER'], "certificates.pdf"))

    try:
        start_time = time.time()
        generate_certificate_pdf(dataT, processed_seat_numbers, output_pdf_path, year, course_name, signature_file)

        response = send_file(output_pdf_path, as_attachment=True, download_name="certificates.pdf")

        with status_lock:
            status['message'] = "Completed"
        remove_checkpoint()
        end_time = time.time()
        print(f" Total FPDF2 Time taken: {end_time - start_time} seconds")

    except Exception as e:
        print(f"Error generating certificates: {e}")
        with status_lock:
            status['message'] = "Error generating certificates"
        return "Error generating certificates", 500

    finally:
        os.remove(ms6_file_path)
        os.remove(bms_file_path)

    return response


# Load the course Excel file statically when the server starts
df_courses = pd.read_excel('EXAM.xls')

@app.route('/get-courses', methods=['GET'])
def get_courses():
    course_names = df_courses['EXAM_NAME'].tolist()
    return jsonify(course_names)

def generate_certificate_pdf(dataT, processed_seat_numbers, output_pdf_path, year, course_name, signature_path):
    # Remove rows where 'SEAT_NO' is already processed or duplicates exist
    dataT = dataT.drop_duplicates(subset=['SEAT_NO'])
    dataT = dataT[~dataT['SEAT_NO'].isin(processed_seat_numbers)]

    pdf = FPDF(unit='pt', format='A4')

    margin = 105   # 105 point margin
    desired_width = 390  # Adjust as needed
    desired_height = 375  # Adjust as needed

    template_image_path = TEMPLATE_PATH
    pdf.set_auto_page_break(auto=False, margin=0)  # Disable auto page breaks

    y_positions = [20, 445]  # Y-positions for two certificates on the page
    current_y_index = 0  # Track current position for the next certificate

    # Pre-load the template image and set font and colors
    template_image = template_image_path  # Template path
    pdf.set_font("Times", size=11)
    gray_color = (128, 128, 128)
    black_color = (0, 0, 0)


    try:
        for index, student in dataT.iterrows():
            seat_number = student['SEAT_NO']  # Get the seat number for checkpointing

            if current_y_index == 0:  # Add a new page if needed
                pdf.add_page()

            # Determine y-position for current certificate
            y_position = y_positions[current_y_index]
            current_y_index = (current_y_index + 1) % 2  # Toggle between 0 and 1

            # Draw the certificate template
            # pdf.image(template_image, x=margin, y=y_position, w=desired_width, h=desired_height)

            # Prepare student details
            heading = "University of Mumbai"
            certify = "I Certify that"
            name = str(student['NAME']).strip() if pd.notnull(student['NAME']) else 'N/A'
            coll_no = str(student['COLL_NO'])
            pno = str(student['pno'])
            ccf = f"CCF : {coll_no} : {pno}"
            seat_no = "NO : " + str(student['SEAT_NO']).strip() if pd.notnull(student['SEAT_NO']) else 'N/A'
            gender = "/ - FEMALE" if pd.notnull(student['Gender']) and student['Gender'] == 'FEMALE' else ''
            name_with_gender = f"/ {name}" if gender else name
            thirdline = "held by the University of Mumbai in the month of"
            director = "DIRECTOR"
            board = "BOARD OF EXAMINATIONS & EVALUATION"

            current_date = datetime.now().strftime("%B %d, %Y")

            if 'CGPA' in student:
                cgpa = str(student['CGPA']) if pd.notnull(student['CGPA']) else 'N/A'
                course_semester_text = f"PASSED THE {course_name} (CBCGS) EXAMINATION"
                date_text = f"{year} WITH {cgpa} CGPI"
            elif 'CGRADE' in student:
                grade = str(student['CGRADE']) if pd.notnull(student['CGRADE']) else 'N/A'
                course_semester_text = f"PASSED THE {course_name} (CBSGS) EXAMINATION"
                date_text = f"{year} AND WAS PLACED IN THE {grade} GRADE"

            # Draw the university logo
            logo_width = 50  # Adjust as needed
            logo_height = 52  # Adjust as needed
            logo_x = margin + 170  # Adjust x position as needed
            logo_y = y_position + 43  # Adjust y position as needed
            pdf.image(logo_path, x=logo_x, y=logo_y, w=logo_width, h=logo_height)

            # Draw the director's signature
            signature_width = 100  # Adjust as needed
            signature_height = 40  # Adjust as needed
            signature_x = margin + desired_width - signature_width - 70  # Adjust x position as needed
            signature_y = y_position + desired_height - signature_height - 25  # Adjust y position as needed
            pdf.image(signature_path, x=signature_x, y=signature_y, w=signature_width, h=signature_height)

            # Draw text onto the PDF (grouped by font/color to minimize state changes)
            pdf.set_text_color(*gray_color)
            pdf.set_font("Times", size=11)

            # CCF and Seat Number
            pdf.set_xy(140, y_position + 72)
            pdf.cell(0, 40, ccf)

            pdf.set_xy(140, y_position + 87)
            pdf.cell(0, 40, seat_no)

            name_width = pdf.get_string_width(name_with_gender)
            max_name_width = desired_width - margin  # Adjust the max width based on your template

            text_width = pdf.get_string_width(course_semester_text)
            max_text_width = desired_width - margin  # Adjust width based on template
            
            # Adjust the position if course_semester_text is wider than name
            if text_width > max_text_width:  # Add a gap if text width is greater than name width
                pdf.set_xy(150, y_position + 195)
                pdf.multi_cell(max_text_width, 15, course_semester_text, align='L')

                if name_width > max_name_width:
                    pdf.set_xy(150, y_position + 160)
                    pdf.multi_cell(max_name_width, 15, name_with_gender, align='L')  # Wrap text to next line
                else:
                    pdf.set_xy(150, y_position + 160)
                    pdf.cell(0, 40, name_with_gender)

            else:
                pdf.set_xy(150, y_position + 195)
                pdf.cell(0, 40, course_semester_text)

                if name_width > max_name_width:
                    pdf.set_xy(150, y_position + 167)
                    pdf.multi_cell(max_name_width, 15, name_with_gender, align='L')  # Wrap text to next line
                else:
                    pdf.set_xy(150, y_position + 170)
                    pdf.cell(0, 40, name_with_gender)

            # Third line and date text
            pdf.set_font("Helvetica", style='', size=12)
            pdf.set_text_color(*black_color)

            pdf.set_xy(150, y_position + 220)
            pdf.cell(0, 40, thirdline)

            pdf.set_xy(265, y_position + 110)
            pdf.cell(0, 40, certify)

            pdf.set_font("Times", size=11)
            pdf.set_text_color(*gray_color)

            pdf.set_xy(150, y_position + 246)
            pdf.cell(0, 40, date_text)

            # Gender and Date
            pdf.set_xy(130, y_position + 320)
            pdf.cell(0, 40, gender)

            pdf.set_xy(120, y_position + 340)
            pdf.cell(0, 40, current_date)

            # Add font only if it hasn't been added yet
            if 'OldLondon' not in pdf.fonts:
                pdf.add_font('OldLondon', '', r'OldLondon.ttf')

            pdf.set_font("OldLondon", size=26)
            pdf.set_text_color(*black_color)
            pdf.set_xy(194, y_position + 3)
            pdf.cell(0, 40, heading)

            # Revert font to regular for subsequent text if needed
            pdf.set_font("Helvetica", style='', size=11)

            # save_checkpoint(seat_number, "certificate_generation")
            
        # Save the final merged PDF
        pdf.output(output_pdf_path)

        with status_lock:
            status['message'] = "Completed"

    except Exception as e:
        print(f"Error generating certificates: {e}")
        with status_lock:
            status['message'] = f"Error: {e}"


def delete_files_in_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)


if __name__ == '__main__':
    app.run(debug=True)
