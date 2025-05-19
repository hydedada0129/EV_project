#!/usr/bin/env python3
import os
import dropbox
# from dotenv import load_dotenv
import mysql.connector
import datetime
from openpyxl import load_workbook
from datetime import datetime
from dropbox.files import WriteMode
# from secrets_loader import get_secret
from upload_to_db import upload_file_to_dropbox
# from crontab import CronTab

#TO DO: requirements.txt
#save your excel template in project root folder

#connect to MySQL
DB_CONFIG = {
    'host':     '127.0.0.1',         #local machine's mysql
    'port':     3007,                #local machine's port      
    'user':     'wpuser',
    'password': 'wppassword',
    'database': 'wpdb',
}

TEMPLATE_PATH = 'Report_Template_without_pics.xlsx'
#TO DO: output file format= machineName_id_datetime_
OUTPUT_PATH = f'filled_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

def fetch_latest_submission(submission_id=None):
    """Fetch one submission record from the database."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT id, user_id, field_1, field_2, created_at
        FROM wp_submissions
        WHERE created_at >= NOW() - INTERVAL 1 DAY
    """

    cursor.execute(sql)
    row = cursor.fetchall()
    cursor.close()
    conn.close()
    return row

# function: fill value into Excel
def fill_excel(row, output_path):
    """load the template, write data into cells, and save a new file"""
    if not row:
        raise ValueError("no data found in the database.")
    wb = load_workbook(TEMPLATE_PATH)
    ws = wb.active

    ws['H22'] = row['field_1']
    ws['A34'] = row['field_2']

    wb.save(output_path)
    print(f'generated excel file: {output_path}')

def main():
    try:
        data = fetch_latest_submission()
        # print(data)
        if not data:
            raise ValueError("New report is not found.")

        for row in data:
            output_path = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

            fill_excel(row, output_path)
            
            dest = upload_file_to_dropbox(output_path)
            print(f'Excel report has been uploaded: {dest}')

        # 清理本地檔案 (not decide yet, comment it first)
        # os.remove(OUTPUT_PATH)
        # print(f'本地檔案已清理：{OUTPUT_PATH}')

    except Exception as e:
        print(f"執行失敗：{e}")
        exit(1)     #1 : force terminates the whole Python script, and return a non-zero code to Operation System.

if __name__== "__main__":
    main()