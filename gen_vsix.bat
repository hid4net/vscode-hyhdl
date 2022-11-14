@echo off
for /F "delims=" %%a in ('where *.vsix') do (
    del "%%a"
)
vsce package