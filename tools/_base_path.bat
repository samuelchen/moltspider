@echo off

pushd .
cd /d %~dp0
set TOOL_PATH=%cd%
rem echo "TOOL_PATH is %TOOL_PATH%."
pushd ..
set BASE_PATH=%cd%
rem echo "BASE_PATH is %BASE_PATH%."
popd
popd

echo %BASE_PATH%
