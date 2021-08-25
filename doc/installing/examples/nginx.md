# OpenQuake Engine WebUI nginx configuration

To `/etc/nginx/conf.d/webui.conf` add:

```nginx
server {
    listen       443 ssl;
    server_name  server.openquake.local;

    # Maximum upload size
    client_max_body_size 256m;

    access_log  /var/log/nginx/access-webui.log;
    error_log  /var/log/nginx/error-webui.log;

    ssl_certificate     /etc/ssl/ssl.crt;
    ssl_certificate_key /etc/ssl/ssl.key;

    location = / {
        return 301 https://$host/engine; 
    }

    location / {

        proxy_read_timeout 300s;
        proxy_send_timeout 300s;

        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   Host $host;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_redirect     http:// https://;
        proxy_pass         http://127.0.0.1:8800;
    }

    location /static {
        # Run 'python manage.py collectstatic' first
        alias /var/www/webui;
    }

    error_page   500 502 503 504  /50x.html;
    location = /50x.html {
        root   /usr/share/nginx/html;
    }
}
```
