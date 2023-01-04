#!/bin/bash

modules=$1
stage=$2
if [ -n "$stage" ];then
 cd $stage
 
fi
for module in $(echo $modules|tr ',' ' ')
do
 version=noVersion
 if [ -d $module ];then
  if [ -f ${module}/__manifest__.py ];then
   fileVersion=$(grep "[\'\"]version[\'\":]" ${module}/__manifest__.py|grep [0-9]|head -1)
   if [ -n "$fileVersion" ];then
    version=$(echo $fileVersion|cut -f2 -d:|sed "s/[ ,\"\'\n\r]*//g")
   fi
  else
   version=noManifest
  fi

 else
  if [ -z "$stage" ];then
   version=0
  fi
 fi
 if [ -z "$answer" ];then
  answer=${module}:${version}
 else
  answer=${answer},${module}:${version}
 fi
done
echo $answer
