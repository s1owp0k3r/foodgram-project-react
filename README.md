# Приложение Kittygram в docker-контейнерах
## Описание проекта
Проект Kittygram создан для публикации котиков! 
## GitHub Actions workflow status
![Main Kittygram workflow](https://github.com/s1owp0k3r/kittygram_final/actions/workflows/main.yml/badge.svg)
## Как развернуть приложение на удаленном сервере
- Склонируйте репозиторий github:
```
git clone git@github.com:s1owp0k3r/kittygram_final.git
```
- Создайте в рабочей директории сервера папку kittygram
- Скопируйте в папку kittygram файлы docker-compose.production.yml
и .env.example, внесите в .env.example нужные значения и переименуйте в .env
- Установите на сервер Docker Compose:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```
- Установите и настройте nginx:
```
sudo apt install nginx -y
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```
- Скопируйте в файл файл конфигурации nginx /etc/nginx/sites-enabled/default
следующие настройки:
```
server {
    server_name <ваш домен>;
    server_tokens off;

    location / {
        proxy_pass http://127.0.0.1:9000;
    }
}
```
- Установите certbot на сервер и получите SSL-сертификат:
```
sudo apt install snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx
sudo systemctl reload nginx
```
- Перейдите в папку kittygram и запустите приложение через Docker Compose:
```
sudo docker compose -f docker-compose.production.yml up -d
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
# Авторы проекта
Борис Градов и команда Яндекс.Практикум