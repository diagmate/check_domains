#!/bin/bash
# https://www.domcop.com/top-10-million-domains
wget -c https://www.domcop.com/files/top/top10milliondomains.csv.zip
if [ -f top10milliondomains.csv.zip ]; then
	unzip -q top10milliondomains.csv.zip
fi