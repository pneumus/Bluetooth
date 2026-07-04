pacman -S pyside6 qt6-connectivity   
sudo setcap cap_net_raw,cap_net_admin+eip $(readlink -f $(which python))
