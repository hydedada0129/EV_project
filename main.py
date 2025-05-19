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

# function: fill value into Excel
def fill_excel(row):
    """load the template, write data into cells, and save a new file"""
    if not row:
        raise ValueError("no data found in the database.")
    wb = load_workbook(TEMPLATE_PATH)
    ws = wb.active

    ws['H22'] = row['field_1']
    ws['A34'] = row['field_2']

    wb.save(OUTPUT_PATH)
    print(f'generated excel file: {OUTPUT_PATH}')

def main():
    try:
        data = fetch_latest_submission()
        if not data:
            raise ValueError("New report is not found.")
        #fill the submission data into Excel report (OUTPUT_PATH)
        fill_excel(data)        

        #upload to Dropbox
        dest = upload_file_to_dropbox(OUTPUT_PATH)

        print(f"output path: {OUTPUT_PATH}")

        print(f'Excel report has been uploaded: {dest}')

        # 清理本地檔案 (not decide yet, comment it first)
        # os.remove(OUTPUT_PATH)
        # print(f'本地檔案已清理：{OUTPUT_PATH}')

    except Exception as e:
        print(f"執行失敗：{e}")
        exit(1)     #1 : force terminates the whole Python script, and return a non-zero code to Operation System.

# def schedule_task():
#     # Initialize CronTab for current user in Docker container
#     cron = CronTab(user=True)
#     # Remove existing cron jobs to avoid duplicates
#     cron.remove_all()
#     # Create new cron job to run 'python /app/main.py --run' every minute
#     job = cron.new(command='/home/oem/wordpress-docker/.venv/bin/python /home/oem/wordpress-docker/main.py --run')
#     # Set schedule: every minute
#     job.setall('* * * * *')
#     # Write cron job to system
#     cron.write()
#     print("Cron job scheduled: Every minute")

if __name__== "__main__":
    main()

# if __name__ == '__main__':
#     import sys
#     if len(sys.argv) > 1 and sys.argv[1] == '--run':
#         process_submissions()
#     else:
#         schedule_task()