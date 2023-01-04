#!/bin/bash

container=$(sudo docker ps|grep -E "registry.metroscales.io/odooerp"|awk '{print $1}')
if [ -n "$container" ];then
    sudo docker restart $container 
else
    echo "Container not found."
fi
