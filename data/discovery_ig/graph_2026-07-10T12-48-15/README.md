# Instagram graph-walk run — 2026-07-10

`audience_SUPERSEDED_no_signal_quality.json` was produced BEFORE the classifier could say
"this channel carries no signal". It labels @zozrsl as 0% pro / general_consumer / High confidence,
which is wrong: his comments are single-word lead-magnet replies ("Guide", "Niche"), i.e. a
comment-to-DM mechanic, not an audience. His bio reads "Revendeur Vinted à plein temps (+100K€)".

Do not use it. Re-run `scripts/classify_audience.py --run-dir <this dir>` once Anthropic credit is
restored; the schema now carries `signal_quality: usable|insufficient|polluted`.

Also note: @juliacrcl classifies as pro_reseller on TikTok and general_consumer on Instagram.
Same person, same week. audience_mix is a property of platform:handle, not of the person.
