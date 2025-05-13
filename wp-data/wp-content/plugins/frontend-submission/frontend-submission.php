<?php
/**
 * Plugin Name: Frontend Data Submission
 * Description: 讓已登入使用者在前端填寫表單並把資料儲存到自訂資料表。
 * Version: 1.0
 * Author: 你的名字
 */

if ( ! defined( 'ABSPATH' ) ) exit;

// 建立自訂資料表
register_activation_hook( __FILE__, function() {
    global $wpdb;
    $table = $wpdb->prefix . 'submissions';
    $charset = $wpdb->get_charset_collate();
    $sql = "CREATE TABLE $table (
      id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
      user_id    BIGINT UNSIGNED NOT NULL,
      field_1    VARCHAR(255)     NOT NULL,
      field_2    TEXT             NOT NULL, 
      created_at DATETIME         DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (id)
    ) $charset;";
    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta( $sql );
} );

// 短碼顯示表單
add_shortcode( 'frontend_submission', function() {
    // if ( ! is_user_logged_in() ) {
    //     return '<p>請先 <a href="' . esc_url( wp_login_url( get_permalink() ) ) . '">登入</a>。</p>';
    // }
    
    // 如果未登录，直接显示登录表单
    if ( ! is_user_logged_in() ) {
        ob_start();
        wp_login_form();
        return ob_get_clean();
    }
    
    global $wpdb;
    $table = $wpdb->prefix . 'submissions';
    $output = '';

    if ( $_SERVER['REQUEST_METHOD'] === 'POST' && isset( $_POST['fs_submit'] ) && wp_verify_nonce( $_POST['fs_nonce'], 'fs_action' ) ) {
        $user_id = get_current_user_id();
        $f1 = sanitize_text_field( $_POST['field_1'] );
        $f2 = sanitize_textarea_field( $_POST['field_2'] );
        $wpdb->insert( $table, [
            'user_id' => $user_id,
            'field_1' => $f1,
            'field_2' => $f2,
        ] );
        $output .= '<p>資料已儲存！</p>';
    }

    $output .= '<form method="post">';
    $output .= wp_nonce_field( 'fs_action', 'fs_nonce', true, false );
    $output .= '<p><label>Charger\'s Serial Number<br><input type="text" name="field_1" required></label></p>';
    $output .= '<p><label>Performed Description<br><textarea name="field_2" rows="4" required></textarea></label></p>';
    $output .= '<p><button type="submit" name="fs_submit">送出</button></p>';
    $output .= '</form>';

    return $output;
} );
