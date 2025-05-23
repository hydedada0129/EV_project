front-end plugins path:
/home/oem/wordpress-docker/wp-data/wp-content/plugins/frontend-submission/frontend-submission.php

photo_url:
/wp-data/wp-content/loads/20205/05
need to change permission from root to www-data, otherwise, you can't save images into this folder!!!!!

packing docker compose:
docker-compose down
docker save -o wp-mysql.tar your_container_image
# 备份MySQL数据（需要sudo）
sudo tar -czvf db-data.tar.gz ./db-data
# 备份WordPress数据（通常不需要sudo）
tar -czvf wp-data.tar.gz ./wp-data
tar -czvf wp-config.tar.gz docker-compose.yml uploads.ini

# security groups(ssh), local ip, .pem
scp -i your-key.pem wp-mysql.tar wp-data.tar.gz wp-config.tar.gz ec2-user@your-ec2-ip:/home/ubuntu/


# 載入映像
docker load -i wp-mysql.tar

# 解壓設定檔
tar -xzvf wp-config.tar.gz

# 解壓資料卷（保持相同路徑結構）
sudo tar -xzvf wp-data.tar.gz -C /home/ec2-user/

# 啟動服務（自動使用已存在的卷資料）
docker-compose up -d