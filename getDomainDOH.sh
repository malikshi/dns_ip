#!/bin/bash

# Fetch Lists
curl -s https://raw.githubusercontent.com/dibdot/DoH-IP-blocklists/master/doh-domains.txt > doh-domains1.txt
curl -s https://raw.githubusercontent.com/hagezi/dns-blocklists/main/domains/doh.txt > doh-domains2.txt

# Merge and Deduplicate
cat doh-domains1.txt doh-domains2.txt | sort -u | sed '/^[[:space:]]*$/d' | sed '/#/d' | grep -v -i 'apple' | grep -v -i 'icloud' > domains-doh.txt

# Cleanup
rm doh-domains1.txt doh-domains2.txt