@echo off
chcp 65001
REM 遍历子文件夹
REM 结尾是斜杠符\，传进来会把后面的双引号"转义。因此在bat的双引号前加一个空格避免这种情况。
for /r Download %%i in (*.m4b) do ( 
    C:\python311\python.exe AudiobookRename.py -o "%~dp0m4b" "%%i"
    del "%%~dpni.aaxc"
    del "%%~dpni.voucher"
    timeout /t 2
    )
