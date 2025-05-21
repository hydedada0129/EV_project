<?php
/**
 * Plugin Name: Frontend Data Submission
 * Description: 讓已登入使用者在前端填寫表單並把資料與圖片儲存到自訂資料表與伺服器。
 * Version: 1.7
 * Author: 你的名字
 */

// 防止直接存取此檔案
if (!defined('ABSPATH')) exit;

/**
 * 表單提交邏輯處理
 * 使用 WordPress 的 init hook 來處理表單提交
 * 現在寫入資料到 wp_submissions 表格
 */
add_action('init', function () {
    // 檢查是否有表單提交
    if (isset($_POST['fs_submit'])) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'submissions'; // 使用現有的 wp_submissions 表格
        
        // 收集並清理表單提交的資料
        $data = [
            'user_id'          => get_current_user_id(),                        // 當前用戶 ID
            'machine_name'     => sanitize_text_field($_POST['machine_name']),  // 機器名稱
            'job_number'       => sanitize_text_field($_POST['job_number']),    // 工作編號
            'date_submitted'   => sanitize_text_field($_POST['date_submitted']), // 提交日期
            'site_address'     => sanitize_textarea_field($_POST['site_address']), // 地址
            'model_number'     => sanitize_text_field($_POST['model_number']),  // 型號
            'serial_number'    => sanitize_text_field($_POST['serial_number']), // 序號
            'equipment_type'   => sanitize_text_field($_POST['equipment_type']), // 設備類型
            'travel_date'      => sanitize_text_field($_POST['travel_date']),   // 出差日期
            'travel_hours'     => sanitize_text_field($_POST['travel_hours']),  // 出差時數
            'travel_arrived'   => sanitize_text_field($_POST['travel_arrived']), // 到達時間
            'travel_miles'     => sanitize_text_field($_POST['travel_miles']),  // 行駛里程
            'onsite_date'      => sanitize_text_field($_POST['onsite_date']),   // 現場日期
            'onsite_start'     => sanitize_text_field($_POST['onsite_start']),  // 開始時間
            'onsite_end'       => sanitize_text_field($_POST['onsite_end']),    // 結束時間
            'work_description' => sanitize_textarea_field($_POST['work_description']), // 工作描述
            'created_at'       => current_time('mysql'),                        // 當前時間
            // 照片資料會在上傳後更新
        ];
        
        // 將資料插入表格
        $wpdb->insert($table_name, $data);
        $entry_id = $wpdb->insert_id; // 取得插入的 ID
        
        // 記錄插入結果，用於除錯
        if ($entry_id) {
            error_log("成功插入資料，ID: " . $entry_id);
        } else {
            error_log("插入資料失敗: " . $wpdb->last_error);
        }
        
        // 如果有照片上傳且資料成功插入
        if ($entry_id && isset($_FILES['photos']) && !empty($_FILES['photos']['name'][0])) {
            // 載入 WordPress 檔案處理函數
            if (!function_exists('wp_handle_upload')) {
                require_once(ABSPATH . 'wp-admin/includes/file.php');
            }
            
            // 取得上傳的檔案資訊
            $uploaded_files = $_FILES['photos'];
            $photo_urls = [];
            
            // 處理每個上傳的檔案
            foreach ($uploaded_files['name'] as $key => $name) {
                if ($uploaded_files['error'][$key] === UPLOAD_ERR_OK) {
                    // 重新格式化檔案資訊
                    $file = [
                        'name'     => $uploaded_files['name'][$key],
                        'type'     => $uploaded_files['type'][$key],
                        'tmp_name' => $uploaded_files['tmp_name'][$key],
                        'error'    => $uploaded_files['error'][$key],
                        'size'     => $uploaded_files['size'][$key]
                    ];
                    $upload_overrides = ['test_form' => false];
                    $movefile = wp_handle_upload($file, $upload_overrides);
                    
                    // 如果檔案上傳成功
                    if ($movefile && !isset($movefile['error'])) {
                        $photo_urls[] = $movefile['url'];
                    }
                }
            }
            
            // 如果有成功上傳的照片，更新資料列
            if (!empty($photo_urls)) {
                // 將所有照片 URL 合併為逗號分隔的字串
                $photo_url_string = implode(',', $photo_urls);
                
                // 更新資料列，添加照片 URL
                $wpdb->update(
                    $table_name,
                    ['photo_url' => $photo_url_string],
                    ['id' => $entry_id]
                );
                
                error_log("已更新照片 URL: " . $photo_url_string);
            }
        }
        
        // 設定成功訊息
        set_transient('frontend_submission_success_' . get_current_user_id(), true, 60);
        
        // 重新導向
        wp_redirect(remove_query_arg('submitted', wp_get_referer()));
        exit;
    }
});

/**
 * 註冊前端表單短碼
 */
add_shortcode('frontend_submission', function () {
    // 確認使用者已登入
    if (!is_user_logged_in()) {
        return wp_login_form(['echo' => false]);
    }

    // 檢查成功訊息
    $user_id = get_current_user_id();
    $show_success = get_transient('frontend_submission_success_' . $user_id);
    if ($show_success) {
        delete_transient('frontend_submission_success_' . $user_id);
    }

    // 開始輸出緩衝
    ob_start();
    ?>
    <?php if ($show_success): ?>
        <p>資料與圖片已送出成功！</p>
    <?php endif; ?>
    <!-- 前端提交表單 -->
    <form method="post" enctype="multipart/form-data">
        <label>Machine Name:</label>
        <input type="text" name="machine_name" required>

        <label>JOB #:</label>
        <input type="text" name="job_number" required>

        <label>DATE:</label>
        <input type="date" name="date_submitted" required>

        <label>SITE ADDRESS:</label>
        <textarea name="site_address" required></textarea>

        <label>Model #:</label>
        <input type="text" name="model_number" required>

        <label>Serial #:</label>
        <input type="text" name="serial_number" required>

        <label>Equipment Type:</label>
        <input type="text" name="equipment_type" required>

        <label>Travel Date:</label>
        <input type="date" name="travel_date" required>

        <label>Travel Hours:</label>
        <input type="text" name="travel_hours" required>

        <label>Arrived:</label>
        <input type="text" name="travel_arrived" required>

        <label>Travel Miles:</label>
        <input type="text" name="travel_miles" required>

        <label>Onsite Date:</label>
        <input type="date" name="onsite_date" required>

        <label>Start:</label>
        <input type="text" name="onsite_start" required>

        <label>End:</label>
        <input type="text" name="onsite_end" required>

        <label>Work Description:</label>
        <textarea name="work_description" required></textarea>

        <label>上傳照片:</label>
        <input type="file" name="photos[]" multiple accept=".jpg,.jpeg,.png">

        <button type="submit" name="fs_submit">送出</button>
    </form>
    <?php
    return ob_get_clean();
});

/**
 * 添加除錯功能，檢查資料是否正確存入
 */
add_action('admin_menu', function() {
    add_management_page('檢查提交資料', '檢查提交資料', 'manage_options', 'check-submissions', function() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'submissions';
        
        echo '<div class="wrap">';
        echo '<h1>最近提交的資料</h1>';
        
        // 查詢最近的提交
        $entries = $wpdb->get_results("SELECT * FROM $table_name ORDER BY created_at DESC LIMIT 10");
        
        if (empty($entries)) {
            echo '<p>目前沒有提交的資料。</p>';
        } else {
            echo '<table class="widefat">';
            echo '<thead><tr>';
            echo '<th>ID</th>';
            echo '<th>機器名稱</th>';
            echo '<th>工作編號</th>';
            echo '<th>提交日期</th>';
            echo '<th>照片</th>';
            echo '<th>提交時間</th>';
            echo '</tr></thead>';
            echo '<tbody>';
            
            foreach ($entries as $entry) {
                echo '<tr>';
                echo '<td>' . esc_html($entry->id) . '</td>';
                echo '<td>' . esc_html($entry->machine_name) . '</td>';
                echo '<td>' . esc_html($entry->job_number) . '</td>';
                echo '<td>' . esc_html($entry->date_submitted) . '</td>';
                echo '<td>';
                
                // 顯示照片縮圖（如果有）
                if (!empty($entry->photo_url)) {
                    $photos = explode(',', $entry->photo_url);
                    foreach ($photos as $photo) {
                        echo '<a href="' . esc_url($photo) . '" target="_blank">';
                        echo '<img src="' . esc_url($photo) . '" style="max-width: 100px; max-height: 100px; margin: 5px;" />';
                        echo '</a>';
                    }
                } else {
                    echo '無照片';
                }
                
                echo '</td>';
                echo '<td>' . esc_html($entry->created_at) . '</td>';
                echo '</tr>';
            }
            
            echo '</tbody></table>';
        }
        
        echo '</div>';
    });
});