#!/bin/sh
OUTPUT=`git submodule update --remote`
if [[ -z $OUTPUT ]]; then
	echo "Nothing done"
fi
