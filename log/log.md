# Log list

[TOC]

## 备份

1.  备份 `\home\pi` 到本地的 `\pihome-20150227`
2.  备份SD卡镜像到本地的 `F:\pi\raspbian_backup_20150227.rar`  
    工具： [win32diskimager]

## 写入镜像

1.  下载镜像到本地的 `F:\pi\2015-02-16-raspbian-wheezy.zip`
2.  写入镜像到SD卡  
    工具： [win32diskimager]

## 初次登录

1.  编辑SD卡上的`cmdline.txt`，给Pi分配静态IP地址  
    添加 `ip=192.168.100.100`
2.  给PC网卡分配静态IP地址192.168.100.1
3.  用网线连接（网卡自动跳线），启动Pi
4.  用SSH登录192.168.100.100，默认用户pi，密码raspberry
5.  执行`sudo raspi-config`，执行`Expand Filesystem`

## 初次配置

### Pi自动连接到无线网络

1.  在Pi上执行`sudo nano /etc/network/interfaces`
2.  编辑`interfaces`文件：

    ```
    auto lo

    iface lo inet loopback
    iface eth0 inet dhcp

    allow-hotplug wlan0
    auto wlan0

    iface wlan0 inet dhcp
       wpa-ssid "poi"
       wpa-psk "na*no*de*su*"
    ```

    即可配置为自动连接SSID为`poi`，密码为`na*no*de*su*`的无线网络。

3.  在主机上建立批处理`enableHostedNetworkPi.bat`：

    ```
    echo
    netsh wlan set hostednetwork mode=allow ssid="poi" key=na*no*de*su*
    netsh wlan start hostednetwork
    pause
    ```
    
4.  在主机上执行批处理，并开启网络共享  
    网络共享将在192.168.137.1区段开启DHCP服务
5.  在Pi上执行`sudo /etc/init.d/networking restart`  
    结果![][img2]
6.  关闭Pi，拔掉网线。

### 用无线网络连接到Pi

1.  开启Pi。等待连接到无线网络。
2.  在主机上，用`arp -a`查看ARP缓存，在192.168.137.1网段确认Pi的IP地址。
3.  SSH之。

### 修改密码

1.  在Pi上执行`passwd`，Pi...Pi....u

### 配置ssh

1.  在Pi上执行`sudo nano /etc/ssh/sshd_config`
2.  编辑`PermitRootLogin no`

### 更新软件包

1.  在Pi上执行`sudo apt-get update`

### 配置Samba

1.  在Pi上执行`sudo apt-get install samba samba-common-bin`
2.  在Pi上编辑`sudo nano /etc/samba/smb.conf`  
    添加段：

    ```
    [pihome]
       commet = pi's home dir 
       path = /home/pi/
       browseable = yes
       read only = no
    ```

3. 添加samba用户：`sudo smbpasswd -a pi`，密码Pi...Pi....u
4. 重启samba服务：`sudo service samba restart`
5. 在主机上用用户`pi`访问即可。

- - -

[win32diskimager]: http://www.raspberry-projects.com/pi/pi-operating-systems/win32diskimager

[img1]: img1.jpg

[img2]: img2.png
