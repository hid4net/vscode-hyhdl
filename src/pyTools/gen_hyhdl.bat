@REM pyinstaller -F hyhdl.py
@REM copy /Y .\dist\hyhdl.exe hyhdl.exe

@REM workon hyhdl
pyinstaller -F hyhdl.py --distpath ./
@REM deactivate