[app]
title = SocketChatApp
package.name = socketchatapp
package.domain = org.socketchat

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,html,css

version = 1.0.0
requirements = python3,flask,pywebview

[buildozer]
log_level = 2
warn_on_root = yes

[android]
api = 33
minapi = 21
ndk = 25.2.9519653

[android:app]
orientation = portrait

[android:permission.INTERNET]
[android:permission.WRITE_EXTERNAL_STORAGE]