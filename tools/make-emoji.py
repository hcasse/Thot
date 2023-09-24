#!/usr/bin/python3

import json
import sys

data = json.load(sys.stdin)
emojis = data["emojis"]
map = {}
for emo in emojis:
	short_name = emo["shortname"]
	if short_name == "":
		print("WARNING: no shortname for", emo["name"])
	else:
		map[short_name] = emo["emoji"]

#for name, chr in map.items():
#	print(name, "->", chr)
	
keys = list(map.keys())
keys.sort()
for key in keys:
	print('\t"%s": "%s",' % (key, map[key]))
