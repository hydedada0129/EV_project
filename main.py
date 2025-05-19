import os
import dropbox
import mysql.connector
from openpyxl import load_workbook
from datetime import datetime
from dropbox.files import WriteMode
from secrets_loader import get_secret
from upload_to_db import upload_file_to_dropbox
from fastapi import FastAPI

app = FastAPI()

# connect to MySQL
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3007,
    'user': 'wpuser',
    'password': 'wppassword',
    'database': 'wpdb',
}

TEMPLATE_PATH = '/home/oem/wordpress-docker/Report_Template_without_pics.xlsx'
OUTPUT_FOLDER = '/home/oem/wordpress-docker/reports'
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def fetch_latest_submission(submission_id=None):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT id, user_id, field_1, field_2, created_at FROM wp_submissions"
    params = ()
    if submission_id:
        sql += " WHERE id = %s"
        params = (submission_id, )
    sql += " ORDER BY created_at DESC LIMIT 1"
    cursor.execute(sql, params)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def fill_excel(row, output_path):
    if not row:
        raise ValueError("no data found in the database.")
    wb = load_workbook(TEMPLATE_PATH)
    ws = wb.active

    ws['H22'] = row['field_1']
    ws['A34'] = row['field_2']

    wb.save(output_path)
    print(f'generated excel file: {output_path}')


def run_report():
    filename = f'filled_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    output_path = os.path.join(OUTPUT_FOLDER, filename)

    data = fetch_latest_submission()
    if not data:
        raise ValueError("New report is not found.")

    fill_excel(data, output_path)
    dest = upload_file_to_dropbox(output_path)
    print(f'Excel report has been uploaded: {dest}')
    return dest


@app.post("/generate_report")
def generate():
    try:
        dest = run_report()
        return {"status": "success", "dropbox_path": dest}
    except Exception as e:
        return {"status": "error", "message": str(e)}
