#!/bin/sh

time=`date +"%d_%m_%Y"`

mkdir -p ~/python/alcohol-study/backups/
cp ~/python/alcohol-study/alcohol_study.db ~/python/alcohol-study/backups/$time
