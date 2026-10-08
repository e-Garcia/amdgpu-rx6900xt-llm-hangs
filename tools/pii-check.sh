#!/usr/bin/env bash
# pii-check.sh [dir] : fail (exit 1) if anything that looks personal is in the tree. Run before every commit
# (and in CI). Also refuses binary dumps: core files, vmcores, devcoredumps, memory blobs never go in this repo.
D="${1:-.}"; FAIL=0
PRIVATE_WORDS="${PRIVATE_WORDS:-$(cat "$(dirname "$0")/private-words.local" 2>/dev/null | tr '\n' ' ')}"  # local, gitignored list
chk() { local name=$1 re=$2; local hits; hits=$(grep -rInE --exclude-dir=.git --exclude=pii-check.sh --exclude=redact.sh --exclude=private-words.local -e "$re" "$D" || true)
  [ -n "$hits" ] && { echo "FAIL [$name]:"; echo "$hits" | head -10; FAIL=1; }; }
for w in $PRIVATE_WORDS; do chk "private word: $w" "$w"; done
# emails, except inside URLs (public mailing-list archive links contain list addresses)
hits=$(grep -rInP --exclude-dir=.git --exclude=pii-check.sh --exclude=redact.sh --exclude=private-words.local '(?<![/A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' "$D" || true)
[ -n "$hits" ] && { echo "FAIL [email]:"; echo "$hits" | head -10; FAIL=1; }
chk mac '\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b'
chk uuid '\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b'
chk ipv4 '\b(10|100|172|192)\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b'
chk phone '(\+?1[ .-]?)?\(?[0-9]{3}\)?[ .-][0-9]{3}[ .-][0-9]{4}\b'
chk home-path '/home/([a-tv-z]|u[a-rt-z])[a-z0-9_-]*'
B=$(find "$D" -path "$D/.git" -prune -o -type f \( -name 'core*' -o -name '*.dmp' -o -name 'vmcore*' -o -name '*devcoredump*' -o -name '*.bin' -o -name '*.gguf' \) -print)
[ -n "$B" ] && { echo "FAIL [binary dump / blob]:"; echo "$B"; FAIL=1; }
[ $FAIL = 0 ] && echo "pii-check: OK"; exit $FAIL
