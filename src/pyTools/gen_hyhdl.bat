@echo off
workon hyhdl && pyinstaller -F hyhdl.py --distpath ./ &&deactivate