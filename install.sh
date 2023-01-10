#!/bin/bash

set -x

# Install external dependencies
apt update && apt install -y libgpiod2
pip3 install adafruit-circuitpython-dht pyserial

# Deploy Python services
apps="Controller ADC DHT Watering"
cp /dev/null /etc/sudoers.d/SmartGarden
for app in $apps; do
    cp SmartGarden-$app.py /usr/local/bin/SmartGarden-$app
    chmod +x /usr/local/bin/SmartGarden-$app
    if [ -f SmartGarden-$app.service ]; then
        cp SmartGarden-$app.service /etc/systemd/system/SmartGarden-$app.service
        for command in start stop enable disable; do
            echo "pi ALL=(ALL) NOPASSWD: /bin/systemctl $command SmartGarden-$app.service" >> /etc/sudoers.d/SmartGarden
        done
    fi
done
chmod 440 /etc/sudoers.d/SmartGarden
systemctl daemon-reload
for app in $apps; do
    systemctl enable SmartGarden-$app.service
    systemctl restart SmartGarden-$app.service
done

# Deploy additional files
mkdir -p /etc/SmartGarden
cp config.json /etc/SmartGarden/config.json
chown -R pi: /etc/SmartGarden
mkdir -p /var/SmartGarden
chown -R pi: /var/SmartGarden