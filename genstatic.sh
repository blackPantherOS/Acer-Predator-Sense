#pyinstaller -n aps -i app_icon.ico aps.py --exclude PyQt6 --exclude PyQt5 --add-data data:data
pyinstaller aps.spec
cp set_get_undervolt read*.sh dist/aps