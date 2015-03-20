# 自动连接多个SSID

[TOC]

## 记录

`sudo nano /etc/wpa-supplicant/wpa-supplicant.conf`

```sh
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
        ssid="poi"
        key_mgmt=WPA-PSK
        psk="na*no*de*su*"
}
network={
        ssid="lkj-w"
        key_mgmt=WPA-PSK
        psk="llkkjj501"
}
```

`sudo nano /etc/network/interfaces`

```sh
auto lo

iface lo inet loopback
iface eth0 inet dhcp

allow-hotplug wlan0
auto wlan0
iface wlan0 inet dhcp
   wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
```

重启。
