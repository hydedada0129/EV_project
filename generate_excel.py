#!/usr/bin/env python3
import mysql.connector
from openpyxl import load_workbook
from datetime import datetime

#pip install mysql-connector-python openpyxl
#save your excel template in project root folder

#1.connect to MySQL
DB_CONFIG = {
    'host':     '127.0.0.1',       #virtual machine's mysql
    'port':     3007,
    # 'host':     '127.0.0.1',  #local machine's mysql
    # 'port':     3007,         #local machine's port
    'user':     'wpuser',
    'password': 'wppassword',
    'database': 'wpdb',
}

#2.Excel template path and output 
TEMPLATE_PATH = 'Report_Template_without_pics.xlsx'
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

# main: run the script
if __name__== "__main__":
    data = fetch_latest_submission()
    fill_excel(data)