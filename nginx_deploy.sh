# 重要注意事项
# 1.nginx默认以data-wwwy用户组运行，该用户组缺少对root下文件的读写权限，所以一般需要将文件拷贝至/var/www/下
# 2.js脚本中，请求服务的url一定不要写成localhost，因为js是跑在本地浏览器里的，请求本地请求的是用户本地，不是服务器本地
#   这也是反向代理的意义所在，将请求转发到服务器本地

# 构建虚拟环境
cd /var/www/flow_writer/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置nginx配置文件
sudo nano /etc/nginx/sites-available/flow_writer

# 写入配置文件
#server {
#    listen 80;
#    server_name 8.152.197.219;
#
#    # ... 原有的前端 root 和 index 配置 ...
#    root /var/www/my_project/frontend;
#    index index.html;
#
#    location / {
#        try_files $uri $uri/ =404;
#    }
#
#    # --- 新增的反向代理配置 ---
#    location /api/ {
#        proxy_pass http://127.0.0.1:8000; # 将 /api/ 开头的请求转发给 uvicorn
#        proxy_set_header Host $host;
#        proxy_set_header X-Real-IP $remote_addr;
#        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#        proxy_set_header X-Forwarded-Proto $scheme;
#    }
#}

# 将配置文件链接到sites-enabled
sudo ln -s /etc/nginx/sites-available/flow_writer /etc/nginx/sites-enabled

# 重启nginx
sudo systemctl restart nginx

# 查看配置是否正确
sudo nginx -t

# 启动uvicorn
cd /var/www/flow_writer/
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000

# 如果访问站点报404，查看nginx日志
sudo tail -f /var/log/nginx/error.log

