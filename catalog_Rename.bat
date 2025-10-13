@echo off
REM chcp 65001

for /r Download %%i in (*.m4b) do ( 
    C:\python311\python.exe AudiobookRename.py -o "%~dp0m4b" "%%i"
    del "%%~dpni.aaxc"
    del "%%~dpni.voucher"
    timeout /t 2
    )