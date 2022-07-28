#!/bin/bash

curl -sLH "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36" https://www.adidas.com/us/yeezy | grep -oE "product%[a-zA-Z0-9]{6,}" | sed 's/product\%2F//g' | sort -u | sed 's/product\%2F//g' | xargs -I '{}' curl -sLH "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36" "https://www.adidas.com/api/products/{}/availability" | jq '..| if .size? == "12" then .sku,.size,.availability_status else empty end' 2> /dev/null
