#!/usr/bin/env bash
# redact.sh < raw > clean : strip personal/host-identifying data from logs before they enter this repo.
# Replaces: user names / home paths, host + tailnet names, IPv4 (except 127.0.0.1/0.0.0.0), IPv6, MACs,
# UUIDs / boot ids, emails, phone-like numbers, GPU/board serials. Private words (names, hosts) come from tools/private-words.local (gitignored) or $PRIVATE_WORDS.
PRIVATE_WORDS="${PRIVATE_WORDS:-$(cat "$(dirname "$0")/private-words.local" 2>/dev/null | tr '\n' ' ')}"  # local, gitignored list
sed_args=()
for w in $PRIVATE_WORDS; do sed_args+=(-e "s/${w}/<redacted>/Ig"); done
sed -E \
  -e 's#/home/[^/ ]+#/home/user#g' \
  -e 's#/Users/[^/ ]+#/Users/user#g' \
  -e 's/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/<email>/g' \
  -e 's/\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b/<mac>/g' \
  -e 's/\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b/<uuid>/g' \
  -e 's/\b[0-9a-f]{32}\b/<id>/g' \
  -e 's/\b(127\.0\.0\.1|0\.0\.0\.0)\b/__KEEPIP_\1__/g' \
  -e 's/\b([0-9]{1,3}\.){3}[0-9]{1,3}\b/<ip>/g' \
  -e 's/__KEEPIP_([0-9.]+)__/\1/g' \
  -e 's/\b[0-9a-fA-F]{1,4}(:[0-9a-fA-F]{0,4}){3,7}::?[0-9a-fA-F]{0,4}\b/<ipv6>/g' \
  -e 's/(\+?1[ .-]?)?\(?[0-9]{3}\)?[ .-][0-9]{3}[ .-][0-9]{4}\b/<phone>/g' \
  -e 's/([Ss]erial( [Nn]umber)?[^:]*:\s*)\S+/\1<serial>/g' \
  "${sed_args[@]}"
