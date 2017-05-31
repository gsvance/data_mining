#!/bin/bash

# For any given simulation, we want the total yields from the explosion
# These totals are printed to stdout at the end of all burn_query runs
# The slurm .out files from burn_query all have of this output in them
# In principle, we can simply take the yields info from any one of them
# This script exists to do that extraction on all the slurm .out files
# It also checks them against one another to make sure they don't differ

# Last edited 3/28/16 by Greg Vance

# Check for the required sbatch directory and outfile arguments
if [ $# -ne 2 ] ; then
	echo "Usage: ${0} sbatch_dir yields_file"
	exit 1
fi

# Function for trimming down the burn_query output to just the yields
# First argument is the burn_query output, second is the destination
function trim_yields {
	# Check that the function is being called correctly
	if [ $# -ne 2 ] ; then
		echo "Error: trim_yields function called incorrectly"
		exit 1
	fi
	# The yields in the burn_query output have a standard line format:
	#     nn = __ nz = __ mass = _________ (____%)
	# Use grep to find those lines having this pattern to them
	grep 'nn =' "$1" > "$2"
}

# Loop over all of the burn_query output files in the directory
for output in `ls "$1"/slurm.*.ISO*.out` ; do
	# Check if the yields file exists from a past iteration or run
	if [ -e "$2" ] ; then
		# Trim the yields and put them in a temp file
		temp="${1}/../temp_yields.txt"
		trim_yields "$output" "$temp"
		# Check if the temp file differs from the one that exists
		if diff -q "$temp" "$2"; then
			# If not, then remove the temp file and move on
			rm "$temp"
		elif [ -s "$temp" ]; then
			# If it does, then we have a big problem
			echo "File ${temp} differs and was not removed!"
			exit 2
		else
			# The temp file is just empty, remove it and continue
			rm "$temp"
		fi
	# If it doesn't exist (first loop iteration), then create it
	else
		trim_yields "$output" "$2"
	fi
done

# At this point, a yields file should exist and there should be no disputes
# Do one last check for the yields file in case the loop iterated zero times
if [ -e "$2" ] ; then
	echo "Yields have been extracted to ${2}"
	exit 0
else
	echo "Error: no yields file could be created"
	exit 1
fi

