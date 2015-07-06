#!/bin/sh

file="/website_files/index.html"
if [ -f "$file" ]
then
  echo "$file found."
else
  echo "$file not found."
  echo "Copying default index.html..."
  cp /index.html /website_files/index.html
fi

sed -i "s/listen 80/listen $PORT/" /etc/nginx/nginx.conf
/usr/sbin/nginx
