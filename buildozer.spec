[app]

# (str) Title of your application
title = JSR Taxi Bill

# (str) Package name
package.name = jsrtaxibill

# (str) Package domain (needed for android packaging)
package.domain = com.jsrtravels

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy,reportlab,pillow

# (list) Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Automatically accept SDK license
android.accept_sdk_license = True

# (list) Target architecture (targeting 64-bit speeds up builds and avoids legacy 32-bit download mirrors)
android.archs = arm64-v8a

# (str) Use latest python-for-android recipe mirrors
p4a.branch = master

# (str) Supported orientation
orientation = portrait

# (bool) Fullscreen mode
fullscreen = 0

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug with command output)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
