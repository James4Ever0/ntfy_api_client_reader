# this will burst
# max/urgent, high, default, low, min
# https://docs.ntfy.sh/publish/

curl \
  -H "Title: Unauthorized access detected" \
  -H "Priority: urgent" \
  -H "Tags: warning,skull" \
  -d "Remote access to phils-laptop detected. Act right away." \
  ntfy.sh/crysis_or_panic
