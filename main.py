#!/usr/bin/env python3
import os
import mysql.connector
import datetime
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as XLImage
from PIL import Image as PILImage
from upload_to_db import upload_file_to_dropbox

# connect to MySQL
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3007,
    'user': 'wpuser',
    'password': 'wppassword',
    'database': 'wpdb',
}

TEMPLATE_PATH = 'Report_Template_without_pics.xlsx'
PHOTO_POSITIONS = ["M5", "S5", "Y5", "M26", "S26", "Y26", "M47", "S47", "Y47"]


def fetch_latest_submission():
    """直接從 wp_submissions 表格獲取最新提交的資料"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # 只查詢 wp_submissions 表格，不再嘗試查詢 wp_submission_data
    sql = """
        SELECT id, user_id, machine_name, job_number, date_submitted, site_address,
               model_number, serial_number, equipment_type,
               travel_date, travel_hours, travel_arrived, travel_miles,
               onsite_date, onsite_start, onsite_end, work_description, 
               created_at, photo_url
        FROM wp_submissions
        WHERE created_at >= NOW() - INTERVAL 5 MINUTE
    """
    
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        if not rows:
            print("在過去 5 分鐘內未找到新提交的資料。嘗試獲取最近的資料...")
            
            # 如果沒有找到最近 5 分鐘的資料，獲取最新的一筆資料
            sql_latest = """
                SELECT id, user_id, machine_name, job_number, date_submitted, site_address,
                       model_number, serial_number, equipment_type,
                       travel_date, travel_hours, travel_arrived, travel_miles,
                       onsite_date, onsite_start, onsite_end, work_description, 
                       created_at, photo_url
                FROM wp_submissions
                ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(sql_latest)
            rows = cursor.fetchall()
            
            if rows:
                print(f"找到最新的一筆資料，ID: {rows[0]['id']}, 時間: {rows[0]['created_at']}")
        
        return rows
    finally:
        cursor.close()
        conn.close()


def resize_image_to_fit(img_path, max_width=320, max_height=400):
    """縮放圖片以適合 Excel 中的大小要求"""
    with PILImage.open(img_path) as img:
        img.thumbnail((max_width, max_height), PILImage.Resampling.LANCZOS)
        resized_path = f"temp_resized_{os.path.basename(img_path)}"
        img.save(resized_path)
        return resized_path


def download_images(photo_urls):
    """下載圖片到臨時資料夾"""
    if not photo_urls:
        print("沒有照片需要下載")
        return []
        
    # 確保 photo_urls 是字串，如果是則分割成列表
    if isinstance(photo_urls, str):
        photo_urls = photo_urls.split(',')
    
    os.makedirs("temp_photos", exist_ok=True)
    local_paths = []
    for idx, url in enumerate(photo_urls):
        try:
            import requests
            url = url.strip()
            if not url:  # 跳過空白 URL
                continue
                
            print(f"下載圖片 {idx+1}/{len(photo_urls)}: {url}")
            response = requests.get(url)
            if response.status_code == 200:
                img_path = f"temp_photos/image_{idx}.jpg"
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                local_paths.append(img_path)
                print(f"圖片下載成功: {img_path}")
            else:
                print(f"圖片下載失敗，狀態碼: {response.status_code}")
        except Exception as e:
            print(f"圖片下載失敗: {e}")
    
    print(f"共下載 {len(local_paths)} 張圖片")
    return local_paths


def cleanup_temp_photos():
    """清理臨時照片資料夾"""
    import shutil
    if os.path.exists("temp_photos"):
        shutil.rmtree("temp_photos")
        print("已刪除 temp_photos 資料夾。")
    
    # 清理暫存的縮放圖片
    for file in os.listdir('.'):
        if file.startswith('temp_resized_'):
            try:
                os.remove(file)
                print(f"已刪除暫存圖片: {file}")
            except Exception as e:
                print(f"刪除暫存圖片失敗: {e}")


def fill_excel(row, output_path):
    """根據提交的資料填充 Excel 模板"""
    if not row:
        raise ValueError("No data found in the database.")

    print(f"處理資料: {row['machine_name']}, ID: {row['id']}")
    
    wb = load_workbook(TEMPLATE_PATH)
    ws = wb.active
    ws.title = row['machine_name']

    # 打印所有欄位，幫助調試
    print("資料欄位:")
    for key, value in row.items():
        print(f"  {key}: {value}")

    # 填充資料到對應的單元格
    ws['G3'] = row['job_number']
    ws['G5'] = row['date_submitted']
    ws['G7'] = row['site_address']
    ws['F22'] = row['model_number']
    ws['H22'] = row['serial_number']
    ws['J22'] = row['equipment_type']
    ws['C27'] = row['travel_date']
    ws['D27'] = row['travel_hours']
    ws['E27'] = row['travel_arrived']
    ws['F27'] = row['travel_miles']
    ws['H27'] = row['onsite_date']
    ws['I27'] = row['onsite_start']
    ws['J27'] = row['onsite_end']
    ws['A34'] = row['work_description']

    # 插入圖片並固定欄寬（防止被圖片自動撐寬）
    fixed_columns = ["M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA"]
    for col in fixed_columns:
        ws.column_dimensions[col].width = 15

    # 處理照片
    if row.get('photo_url'):
        print(f"發現照片: {row['photo_url']}")
        image_paths = download_images(row['photo_url'])
        print(f"下載的圖片數量: {len(image_paths)}")
        
        for i, img_path in enumerate(image_paths[:len(PHOTO_POSITIONS)]):
            try:
                resized_path = resize_image_to_fit(img_path)
                img = XLImage(resized_path)
                ws.add_image(img, PHOTO_POSITIONS[i])
                print(f"已添加圖片到位置 {PHOTO_POSITIONS[i]}")
            except Exception as e:
                print(f"添加圖片失敗: {e}")
    else:
        print("沒有找到照片")

    wb.save(output_path)
    print(f'已生成 Excel 檔案: {output_path}')
    return output_path


def main():
    """主函數，負責整個處理流程"""
    try:
        print("開始獲取最新提交的資料...")
        data = fetch_latest_submission()
        
        if not data:
            print("未找到任何資料。")
            return
            
        print(f"找到 {len(data)} 筆資料")
        
        for row in data:
            # 格式化時間戳記
            if isinstance(row['created_at'], str):
                created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
            else:
                created_at = row['created_at']
                
            created_at_str = created_at.strftime('%Y%m%d_%H%M%S')
            output_path = f"{row['machine_name']}_{created_at_str}.xlsx"
            
            print(f"處理報告: {output_path}")
            filled_file = fill_excel(row, output_path)
            
            try:
                print(f"上傳 Excel 報告到 Dropbox...")
                dest = upload_file_to_dropbox(output_path)
                print(f'Excel 報告已上傳: {dest}')
            except Exception as e:
                print(f"上傳到 Dropbox 失敗: {e}")
                print(f"Excel 報告已生成，但未上傳: {output_path}")

        cleanup_temp_photos()
        print("處理完成")

    except Exception as e:
        print(f"執行失敗：{e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()