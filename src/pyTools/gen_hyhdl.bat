@REM pyinstaller -F hyhdl.py
@REM copy /Y .\dist\hyhdl.exe hyhdl.exe

workon hyhdl && pyinstaller -F hyhdl.py --distpath ./ &&deactivate