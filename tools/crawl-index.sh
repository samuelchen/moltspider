#!/usr/bin/env sh

BASE_PATH=$(cd ../`dirname $0`; pwd)
echo "BASE_PATH is ${BASE_PATH}."

DT=`date +'%y%m%d%H'`
cd ${BASE_PATH}
#echo ">> ${PWD}"
mkdir -p log
nohup scrapy crawl index -s JOBDIR=./jobs/index > log/index-{DT}.log > log/novel${DT}.log &
cd -
#echo "<< ${PWD}"
