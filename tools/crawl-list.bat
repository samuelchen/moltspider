@echo off

set CRAWLER=list

set/p BASE_PATH=|_base_path.bat
set/p LOG=|_log_file.bat %CRAWLER%

pushd %BASE_PATH%
mkdir log 1>nul 2>&1
echo. >>log\%LOG%
echo                    ***** %date% %time% ***** >>log\%LOG%
echo. >>log\%LOG%
scrapy crawl index -s JOBDIR=./jobs/%CRAWLER%  1>>log\%LOG% 2>>&1
popd
