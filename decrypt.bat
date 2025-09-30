@echo off
REM Do not use cmd_decrypt, because extra metadata will be abandoned by FFmpeg. 
REM if using FFmpeg, exiftool -u can restore extra metadata from aaxc to m4b.

timeout /t 5
set AUDIBLE_PLUGIN_DIR=plugins

for %%F in ("Download\*.aaxc") do (
    if EXIST "%%~dpnF.m4b" (
        echo %%F is decrypted.
    ) else (
        audible.exe aaxclean --dir Download "%%F"
    )
)

REM audible.exe aaxclean --dir Download Download\*