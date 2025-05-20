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
    'host': '127.0.0.1', #local machine's mysql
    'port': 3007, #local machine's port
    'user': 'wpuser',
    'password': 'wppassword',
    'database': 'wpdb',
}

TEMPLATE_PATH = 'Report_Template_without_pics.xlsx'
#TO DO: output file format= machineName_id_datetime_

def fetch_latest_submission(submission_id=None):
    """Fetch one submission record from the database."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # 更新SQL查询以匹配新的数据库结构
    sql = """
    SELECT id, user_id, machine_name, job_number, date_submitted, site_address, 
           model_number, serial_number, equipment_type, 
           travel_date, travel_hours, travel_arrived, travel_miles,
           onsite_date, onsite_start, onsite_end, work_description, created_at
    FROM wp_submissions
    WHERE created_at >= NOW() - INTERVAL 1 DAY
    """
    
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

# function: fill value into Excel
def fill_excel(row, output_path):
    """load the template, write data into cells, and save a new file"""
    if not row:
        raise ValueError("No data found in the database.")
    
    wb = load_workbook(TEMPLATE_PATH)
    # print(wb.sheetnames)  # 列出所有工作表名稱
    # print(wb.active)      # 檢查活動工作表

    if not wb.sheetnames:
        raise ValueError("Template Excel file has no sheets.")
    
    # 使用machine_name作为Sheet名称
    # 如果原工作簿中已有同名Sheet，则先删除
    ws = wb[wb.sheetnames[0]]  # 選擇第一個工作表
    # if row['machine_name'] in wb.sheetnames:
    #     del wb[row['machine_name']]
    
    # 重命名活动工作表为machine_name
    ws = wb.active

    ws.title = row['machine_name']

    # 根据指定的单元格位置填充数据
    ws['G3'] = row['job_number']      # JOB #
    ws['G5'] = row['date_submitted']  # DATE
    ws['G7'] = row['site_address']    # SITE ADDRESS
    ws['F22'] = row['model_number']   # Model #
    ws['H22'] = row['serial_number']  # Serial #
    ws['J22'] = row['equipment_type'] # Equipment Type
    ws['C27'] = row['travel_date']    # Travel Date
    ws['D27'] = row['travel_hours']   # Travel Hours (h)
    ws['E27'] = row['travel_arrived'] # Travel Arrived
    ws['F27'] = row['travel_miles']   # Travel Miles
    ws['H27'] = row['onsite_date']    # Onsite Date
    ws['I27'] = row['onsite_start']   # Onsite Start
    ws['J27'] = row['onsite_end']     # Onsite End
    ws['A34'] = row['work_description'] # Work Description
    
    wb.save(output_path)
    print(f'Generated Excel file: {output_path}')
    return output_path

def main():
    try:
        data = fetch_latest_submission()
        # print(data)
        if not data:
            raise ValueError("New report is not found.")
        
        for row in data:
            # 使用machine_name和created_at来命名文件
            created_at_str = row['created_at'].strftime('%Y%m%d_%H%M%S')
            output_path = f"{row['machine_name']}_{created_at_str}.xlsx"
            filled_file = fill_excel(row, output_path)
            dest = upload_file_to_dropbox(output_path)
            print(f'Excel report has been uploaded: {dest}')
            
            # 清理本地檔案 (not decide yet, comment it first)
            # os.remove(output_path)
            # print(f'本地檔案已清理：{output_path}')
            
    except Exception as e:
        print(f"執行失敗：{e}")
        exit(1) #1 : force terminates the whole Python script, and return a non-zero code to Operation System.

if __name__ == "__main__":
    main()
