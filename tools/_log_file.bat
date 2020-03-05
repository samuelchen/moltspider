@echo off
rem set local ENABLEDELAYEDEXPANSION

set NAME=%1

wmic /? > nul || echo "wmic not found." && echo 'quit'

for /f %%i in ( 'wmic os get LocalDateTime /value' ) do (
    echo "%%i" | findstr "LocalDateTime">nul && set DT=%%i
)
set DT=%DT:~14,8%
set LOG=%NAME%-%DT%.log
echo %LOG%


