#!/bin/bash

echo "=================================================="
echo "WordPress Docker 時區測試"
echo "=================================================="
echo ""

# 1. 主機時間
echo "=== 主機時間 ==="
date
echo ""

# 2. WordPress 容器 PHP 時間（最重要）
echo "=== WordPress PHP 時間 ==="
docker exec -it wordpress-docker_wordpress_1 php -r "echo 'PHP 時區: ' . date_default_timezone_get() . PHP_EOL; echo 'PHP 時間: ' . date('Y-m-d H:i:s') . PHP_EOL;"
echo ""

# 3. WordPress 容器系統時間
echo "=== WordPress 系統時間 ==="
docker exec -it wordpress-docker_wordpress_1 date
echo ""

# 4. 檢查 PHP ini 設定
echo "=== PHP 時區設定 ==="
docker exec -it wordpress-docker_wordpress_1 php -r "echo 'PHP ini 時區: ' . ini_get('date.timezone') . PHP_EOL;"
echo ""

# 5. MySQL 時間
echo "=== MySQL 時間 ==="
docker exec -it wordpress-docker_db_1 mysql -u root -prootpassword -e "SELECT NOW() as mysql_time;" 2>/dev/null
echo ""

# 6. 檢查時區設定文件是否存在
echo "=== 檢查時區設定文件 ==="
echo "PHP 時區設定文件:"
if docker exec wordpress-docker_wordpress_1 test -f /usr/local/etc/php/conf.d/timezone.ini; then
    docker exec wordpress-docker_wordpress_1 cat /usr/local/etc/php/conf.d/timezone.ini
else
    echo "時區設定文件不存在"
fi
echo ""

echo "wp-config.php 前5行:"
docker exec wordpress-docker_wordpress_1 head -5 /var/www/html/wp-config.php
echo ""

# 7. 時間差異分析
echo "=== 時間同步檢查 ==="
HOST_TIME=$(date +%s)
PHP_TIME=$(docker exec wordpress-docker_wordpress_1 php -r "echo date('U');")
TIME_DIFF=$((HOST_TIME - PHP_TIME))

if [ $TIME_DIFF -ge -5 ] && [ $TIME_DIFF -le 5 ]; then
    echo "時間同步正常 (差異: ${TIME_DIFF}秒)"
else
    echo "時間不同步 (差異: ${TIME_DIFF}秒)"
fi

echo ""
echo "=================================================="
echo "測試完成"
echo "=================================================="
