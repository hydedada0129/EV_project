<?php
/**
 * Plugin Name: Frontend Data Submission
 * Description: 讓已登入使用者在前端填寫表單並把資料與圖片儲存到自訂資料表與伺服器。
 * Version: 1.8
 * Author: 你的名字
 */
// 防止直接存取此檔案
if (!defined('ABSPATH')) exit;

// 在插件啟動時檢查服務器 PHP 模組
function check_required_php_modules() {
    $missing_modules = [];
    
    // 檢查 GD 庫
    if (!extension_loaded('gd') || !function_exists('imagecreatefrompng')) {
        $missing_modules[] = 'GD 庫 (PNG支援)';
    }
    
    // 檢查檔案上傳功能
    if (!function_exists('move_uploaded_file')) {
        $missing_modules[] = '檔案上傳功能';
    }
    
    // 如果有缺少的模組，顯示警告
    if (!empty($missing_modules)) {
        add_action('admin_notices', function() use ($missing_modules) {
            echo '<div class="error"><p><strong>前端資料提交插件警告：</strong> 您的服務器缺少以下模組，可能影響上傳功能：' . implode(', ', $missing_modules) . '</p></div>';
        });
        
        error_log('前端資料提交插件警告：缺少以下模組：' . implode(', ', $missing_modules));
    }
    
    // 記錄上傳目錄權限
    $upload_dir = wp_upload_dir();
    if (!is_writable($upload_dir['path'])) {
        error_log('上傳目錄無寫入權限: ' . $upload_dir['path']);
        add_action('admin_notices', function() use ($upload_dir) {
            echo '<div class="error"><p><strong>前端資料提交插件警告：</strong> 上傳目錄無寫入權限：' . esc_html($upload_dir['path']) . '</p></div>';
        });
    }
}
register_activation_hook(__FILE__, 'check_required_php_modules');
add_action('admin_init', 'check_required_php_modules');

// 確保 PNG 檔案類型被允許 - 增強版
function ensure_png_upload_support($mimes) {
    // 確認所有可能的 PNG MIME 類型都存在
    $mimes['png'] = 'image/png';
    $mimes['PNG'] = 'image/png';
    $mimes['png'] = 'image/x-png'; // 某些系統使用這種 MIME 類型
    return $mimes;
}
// 提高優先級以確保此函數先執行
add_filter('upload_mimes', 'ensure_png_upload_support', 1);

// 添加新的過濾器來修復 PNG MIME 類型檢測問題
function fix_png_mime_type($data, $file, $filename, $mimes) {
    // 如果是 PNG 檔案但 MIME 類型不正確，強制設置正確的類型
    if (strpos($filename, '.png') !== false || strpos($filename, '.PNG') !== false) {
        $data['ext'] = 'png';
        $data['type'] = 'image/png';
    }
    return $data;
}
add_filter('wp_check_filetype_and_ext', 'fix_png_mime_type', 10, 4);

// 增加上傳檔案大小限制
function increase_upload_file_size($size) {
    // 增加到 10MB
    return 10 * 1024 * 1024; // 10MB in bytes
}
add_filter('upload_size_limit', 'increase_upload_file_size');

/**
 * 表單提交邏輯處理
 * 使用 WordPress 的 init hook 來處理表單提交
 * 現在寫入資料到 wp_submissions 表格
 */
add_action('init', function () {
    // 檢查是否有表單提交
    if (isset($_POST['fs_submit'])) {
        // 添加除錯信息
        error_log('表單提交處理開始');
        
        // 檢查上傳的檔案
        if (isset($_FILES['photos']) && !empty($_FILES['photos']['name'][0])) {
            error_log("檢測到檔案上傳請求，檔案數量：" . count($_FILES['photos']['name']));
            foreach ($_FILES['photos']['name'] as $key => $name) {
                error_log("檔案 {$key}: 名稱={$name}, 類型={$_FILES['photos']['type'][$key]}, 錯誤={$_FILES['photos']['error'][$key]}, 大小={$_FILES['photos']['size'][$key]}");
            }
        }
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'submissions'; // 使用現有的 wp_submissions 表格
        
        // 收集並清理表單提交的資料
        $data = [
            'user_id'          => get_current_user_id(),                        // 當前用戶 ID
            'machine_name'     => sanitize_text_field($_POST['machine_name']),  // 機器名稱
            'job_number'       => sanitize_text_field($_POST['job_number']),    // 工作編號
            'date_submitted'   => sanitize_text_field($_POST['date_submitted']), // 提交日期(working date)
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
            
            // 獲取上傳目錄信息
            $upload_dir = wp_upload_dir();
            
            // 記錄開始處理上傳檔案
            error_log("開始處理檔案上傳，檔案數量: " . count($uploaded_files['name']));
            error_log("上傳目錄: " . $upload_dir['path'] . ", 是否可寫: " . (is_writable($upload_dir['path']) ? '是' : '否'));
            
            // 處理每個上傳的檔案
            foreach ($uploaded_files['name'] as $key => $name) {
                if ($uploaded_files['error'][$key] === UPLOAD_ERR_OK) {
                    // 記錄當前處理的檔案
                    error_log("處理檔案上傳: {$name}, 類型: {$uploaded_files['type'][$key]}");
                    
                    // 重新格式化檔案資訊
                    $file = [
                        'name'     => $uploaded_files['name'][$key],
                        'type'     => $uploaded_files['type'][$key],
                        'tmp_name' => $uploaded_files['tmp_name'][$key],
                        'error'    => $uploaded_files['error'][$key],
                        'size'     => $uploaded_files['size'][$key]
                    ];
                    
                    // 檢查檔案是否存在
                    if (!file_exists($file['tmp_name']) || !is_readable($file['tmp_name'])) {
                        error_log("錯誤: 臨時檔案不存在或無法讀取 - " . $file['tmp_name']);
                        continue;
                    }
                    
                    // 檢查是否為 PNG 檔案
                    $is_png = (strpos($file['name'], '.png') !== false || strpos($file['name'], '.PNG') !== false);
                    
                    if ($is_png) {
                        // 對於 PNG 檔案，使用直接檔案處理方法
                        error_log("檢測到 PNG 檔案，嘗試使用直接檔案處理方法");
                        
                        // 創建唯一的檔案名稱
                        $filename = wp_unique_filename($upload_dir['path'], $file['name']);
                        $new_file = $upload_dir['path'] . '/' . $filename;
                        
                        // 嘗試移動上傳的檔案
                        if (move_uploaded_file($file['tmp_name'], $new_file)) {
                            // 設置適當的檔案權限
                            chmod($new_file, 0644);
                            
                            // 創建 URL
                            $url = $upload_dir['url'] . '/' . $filename;
                            error_log("PNG 檔案直接上傳成功: " . $url);
                            $photo_urls[] = $url;
                        } else {
                            error_log("PNG 檔案直接上傳失敗，錯誤碼: " . error_get_last()['message']);
                        }
                    } else {
                        // 非 PNG 檔案使用 WordPress 內建的上傳處理
                        // 如果是 PNG 檔案，強制設定正確的 MIME 類型
                        if (strpos($file['name'], '.png') !== false || strpos($file['name'], '.PNG') !== false) {
                            $file['type'] = 'image/png';
                        }
                        
                        // 設置上傳選項，明確支援 PNG 等格式
                        $upload_overrides = [
                            'test_form' => false,
                            'mimes'     => [
                                'jpg|jpeg' => 'image/jpeg',
                                'png'      => 'image/png',
                                'PNG'      => 'image/png',
                                'png'      => 'image/x-png',
                                'gif'      => 'image/gif'
                            ]
                        ];
                        
                        $movefile = wp_handle_upload($file, $upload_overrides);
                        
                        // 如果檔案上傳成功
                        if ($movefile && !isset($movefile['error'])) {
                            error_log("檔案上傳成功: {$movefile['url']}");
                            $photo_urls[] = $movefile['url'];
                        } else {
                            error_log("檔案上傳失敗: " . (isset($movefile['error']) ? $movefile['error'] : '未知錯誤'));
                        }
                    }
                } else {
                    // 記錄上傳錯誤
                    $error_messages = [
                        UPLOAD_ERR_INI_SIZE   => '上傳的檔案超過了 php.ini 中 upload_max_filesize 的限制',
                        UPLOAD_ERR_FORM_SIZE  => '上傳的檔案超過了表單中 MAX_FILE_SIZE 的限制',
                        UPLOAD_ERR_PARTIAL    => '檔案只有部分被上傳',
                        UPLOAD_ERR_NO_FILE    => '沒有檔案被上傳',
                        UPLOAD_ERR_NO_TMP_DIR => '找不到臨時資料夾',
                        UPLOAD_ERR_CANT_WRITE => '無法寫入檔案到磁碟',
                        UPLOAD_ERR_EXTENSION  => '檔案上傳被 PHP 擴展停止'
                    ];
                    
                    $error_message = isset($error_messages[$uploaded_files['error'][$key]]) ? 
                                    $error_messages[$uploaded_files['error'][$key]] : 
                                    '未知錯誤';
                    
                    error_log("檔案上傳錯誤 ({$uploaded_files['error'][$key]}): {$error_message}");
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
    <form method="post" enctype="multipart/form-data" onsubmit="return validateFileSize();">
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

        <label>Travel To and From Site</label>

        <label>Travel h:</label>
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

        <label>上傳照片: (每個檔案最大 7MB. Max Qty: 9 images)</label>
        <input type="file" name="photos[]" multiple accept=".jpg,.jpeg,.png" id="photo-upload">
        <p class="file-size-warning" style="color:red;display:none;">檔案過大，請確保每個檔案小於 8MB</p>

        <button type="submit" name="fs_submit">送出</button>
    </form>
    
    <script>
    function validateFileSize() {
        const fileInput = document.getElementById('photo-upload');
        const maxSize = 8 * 1024 * 1024; // 8MB
        const warning = document.querySelector('.file-size-warning');
        
        if (fileInput.files.length > 0) {
            for (let i = 0; i < fileInput.files.length; i++) {
                if (fileInput.files[i].size > maxSize) {
                    warning.style.display = 'block';
                    return false; // 阻止表單提交
                }
            }
        }
        return true;
    }
    </script>
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

/**
 * 檢查和顯示 WordPress 上傳設定資訊
 */
add_action('admin_menu', function() {
    add_management_page('上傳設定資訊', '上傳設定資訊', 'manage_options', 'upload-settings-info', function() {
        echo '<div class="wrap">';
        echo '<h1>WordPress 上傳設定資訊</h1>';
        
        echo '<h2>PHP 設定</h2>';
        echo '<ul>';
        echo '<li>upload_max_filesize: ' . ini_get('upload_max_filesize') . '</li>';
        echo '<li>post_max_size: ' . ini_get('post_max_size') . '</li>';
        echo '<li>memory_limit: ' . ini_get('memory_limit') . '</li>';
        echo '<li>max_execution_time: ' . ini_get('max_execution_time') . ' 秒</li>';
        echo '<li>max_input_time: ' . ini_get('max_input_time') . ' 秒</li>';
        echo '</ul>';
        
        echo '<h2>PHP 模組檢查</h2>';
        echo '<ul>';
        echo '<li>GD 庫: ' . (extension_loaded('gd') ? '已啟用' : '未啟用') . '</li>';
        echo '<li>PNG 支援: ' . (function_exists('imagecreatefrompng') ? '已啟用' : '未啟用') . '</li>';
        echo '<li>檔案上傳功能: ' . (function_exists('move_uploaded_file') ? '已啟用' : '未啟用') . '</li>';
        echo '</ul>';
        
        echo '<h2>WordPress 允許的 MIME 類型</h2>';
        echo '<pre>';
        $mimes = get_allowed_mime_types();
        foreach ($mimes as $ext => $mime) {
            echo "$ext => $mime\n";
        }
        echo '</pre>';
        
        echo '<h2>上傳目錄資訊</h2>';
        $upload_dir = wp_upload_dir();
        echo '<ul>';
        echo '<li>基本目錄: ' . $upload_dir['basedir'] . ' (可寫: ' . (is_writable($upload_dir['basedir']) ? '是' : '否') . ')</li>';
        echo '<li>基本 URL: ' . $upload_dir['baseurl'] . '</li>';
        echo '<li>子目錄: ' . $upload_dir['subdir'] . '</li>';
        echo '<li>目錄: ' . $upload_dir['path'] . ' (可寫: ' . (is_writable($upload_dir['path']) ? '是' : '否') . ')</li>';
        echo '<li>URL: ' . $upload_dir['url'] . '</li>';
        echo '</ul>';
        
        echo '</div>';
    });
});