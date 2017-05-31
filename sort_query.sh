#!/bin/bash

# This script sorts the lines in the CSV files made by burn_query and entropy
# Keeps exactly one header line and sorts the other rows by their particle IDs 
# Not sure if this is necessary for entropy outfiles, but it will work fine
# This is definitely a necessary step for processing the burn_query outfiles
# They are a mess with the IDs out of order and multiple headers in the middle

# Last edited 5/3/16 by Greg Vance

# Check for the infile and outfile arguments
if [ $# -ne 2 ] ; then
	echo "Usage: ${0} query_file sorted_file"
	exit 1
fi

# Print a quick message to the user
echo "Sorting contents of file ${1}"

# Write the first line of the infile to the outfile to keep the header
head -n 1 "$1" > "$2" &&

# Now sort the remainder of the file by ID, grepping to drop the header lines
grep "ID" "$1" --invert-match | sort -n --field-separator="," --key=1 >> "$2"

exit 0

