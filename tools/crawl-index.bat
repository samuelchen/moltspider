@echo off
rem set local ENABLEDELAYEDEXPANSION

pushd .
cd /d %~dp0
set TOOL_PATH=%cd%
echo "TOOL_PATH is %TOOL_PATH%."
pushd ..
set BASE_PATH=%cd%
echo "BASE_PATH is %BASE_PATH%."
popd
popd

wmic /? >> null || echo "wmic not found." && echo 'quit'

for /f %%i in ( 'wmic os get LocalDateTime /value' ) do (
    echo "%%i" | findstr "LocalDateTime">nul && set DT=%%i
)
set DT=%DT:~14,8%
rem echo "%DT%"
set LOG=index-%DT%.log
echo "log is %LOG%"

pushd %BASE_PATH%
mkdir log 1>nul 2>&1
echo. >>log\%LOG%
echo                    ***** %date% %time% ***** >>log\%LOG%
echo. >>log\%LOG%
scrapy crawl index -s JOBDIR=./jobs/index  1>>log\%LOG% 2>>&1
popd
