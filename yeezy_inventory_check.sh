#!/bin/bash

curl -sLH "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36" https://www.adidas.com/us/yeezy%7Cgrep -oE "product%[a-zA-Z0-9]{6,}" | sed 's/product\%2F//g' | xargs -I '{}' curl -sLH "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36" "https://www.adidas.com/api/products/{}/availability" | jq '.variation_list[16] | select(.availability_status | contains("IN_STOCK"))'
