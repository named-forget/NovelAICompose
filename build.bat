@echo off
echo Building NovelAiCompose...

pyinstaller main.py ^
    --name "小说编辑器" ^
    --windowed ^
    --icon="logo.ico" ^
    --add-data="ui/style;ui/style" ^
    --distpath build ^
    --workpath temp^
    --clean

echo.
echo Build finished. Check the 'build' directory.