@echo off
set local SETLOCAL EnableDelayedExpansion

for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do (
  set "DEL=%%a"
)

:start
rem ----- begin ----

set CRAWLER=%1
if "%CRAWLER%" equ "" (
    call :Error "You must specify crawler name (index|list|meta|toc|chapter) at #1 argument."
    exit /b 1
)

exit /b 0

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
set LOG=%CRAWLER%-%DT%.log
echo "log is %LOG%"

pushd %BASE_PATH%
mkdir log 1>nul 2>&1
echo. >>log\%LOG%
echo                    ***** %date% %time% ***** >>log\%LOG%
echo. >>log\%LOG%
scrapy crawl %CRAWLER% -s JOBDIR=./jobs/index  1>>log\%LOG% 2>>&1
popd


rem ----- end -----

goto :eof

rem ---------- functions ----------

:Debug
call :ColorText 08 "%~1"
echo.
goto :eof

:Info
call :ColorText 0b "%~1"
echo.
goto :eof

:Error
call :ColorText 0c "%~1"
echo.
goto :eof


:ColorText
echo off
<nul set /p ".=%DEL%" > "%~2"
findstr /v /a:%1 /R "^$" "%~2" nul
del "%~2" > nul 2>&1
goto :eof
