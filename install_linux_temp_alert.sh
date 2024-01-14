sudo systemctl disable linux-temp-alert
cp linux_temp_alert /usr/bin
cp linux-temp-alert.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start linux-temp-alert
sudo systemctl enable linux-temp-alert
