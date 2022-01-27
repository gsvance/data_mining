#!/usr/bin/env python

# Wrapper for burn_query that takes arguments from command line for a single isotope query
# Eventually, I hope to just rewrite burn_query's interface, but this will help out for now

# Last edited 11 Jan 2021 by Greg Vance

# Example usage:
#	./run_query.py -i 26Al -a 6 -o 26Al.out jet3b/j3b.dir/*.h5
# To search for 26Al above 1e-6 abundance in the jet3b HDF5 files
# Results will be written to a new file named 26Al.out

import argparse
import os
import subprocess
import math

from sn_utils import nn_nz

# User's home directory
HOME_DIR = os.path.expanduser("~")
# Full path to the compiled burn_query executable file
BURN_QUERY_PATH = os.path.join(HOME_DIR, "data_mining/burn_query")

def main():
	# Parse all the arguments using argparse (isotope, abundance, outfile, HDF5s)
	args = parse_args()
	# Translate the arguments into the sequence of inputs that burn_query expects
	inputs = make_inputs(args.isotope, args.abundance, args.outfile)
	# Pass the HDF5 files to burn_query and send the options as a fake input file
	run_burn_query(args.hdf5, inputs)

def parse_args():
	# Create a new argument parser object
	parser = argparse.ArgumentParser()
	# The isotope to query, e.g., 26Al for aluminum-26
	parser.add_argument('-i', '--isotope', required=True)
	# The minimum mass fraction to flag the isotope, e.g., 6 indicates 1e-6
	parser.add_argument('-a', '--abundance', required=True)
	# The new file name for burn_query to write the query to
	parser.add_argument('-o', '--outfile', required=True)
	# The set of HDF5 file(s) that the query is being done on
	parser.add_argument('hdf5', nargs='*')
	# Parse the command line arguments and return them
	return parser.parse_args()

def make_inputs(isotope, abundance, outfile):
	# Determine the values of nn and nz from the isotope argument string
	nn, nz = nn_nz(isotope)
	# Check if the outfile already exists (to avoid overwrites or strange appending behavior)
	if os.path.isfile(outfile):
		# Check what the smallest abundance in the existing file is
		small = get_smallest_abundance(outfile)
		# Let's compare the smallest value to the current requested threshold
		logsmall = math.log10(small) if small is not None else None
		logabun = -1 * int(abundance)
		# If the threshold seems unchanged, then error out
		if logsmall is not None and abs(logsmall - logabun) < 0.5:
			# Raise an error and stop everything! Flag this as an overwrite failure
			error_line_1 = "specified outfile '%s' already exists!\n" % (outfile)
			error_line_2 = "!!! OVERWRITE FAILURE IN RUN_QUERY, BURN_QUERY WAS NOT RUN !!!"
			raise IOError(error_line_1 + error_line_2)
		else:
			# It seems like the threshold has changed, so delete the old file and continue
			os.remove(outfile)
	# Start an empty list to store the inputs for burn_query
	inputs = []
	# Select option 1 (enter a new query)
	inputs.append('1')
	# Enter nn value for the isotope
	inputs.append(nn)
	# Enter nz value for the isotope
	inputs.append(nz)
	# Enter the desired mass fraction threshold
	inputs.append(abundance)
	# Select option 4 (initiate the query)
	inputs.append('4')
	# Confirm the choice to begin the query
	inputs.append('Y')
	# Enter the file name to write the query results
	inputs.append(outfile)
	# Include one trailing newline
	inputs.append('')
	# Join the list with newlines, returning it as one string
	return '\n'.join(inputs)

def get_smallest_abundance(outfile):
	# Initialize a variable to track the smallest mass fraction in the file
	smallest = None
	# Open the older outfile for reading
	with open(outfile, 'r') as outf:
		# Loop over the lines of the ASCII file
		for line in outf:
			# Split the line of the file into columns using ", " as delimiter
			columns = line.strip().split(', ')
			# There should be 4 columns -- if not, quietly move on
			if len(columns) != 4:
				continue
			# If we have a good line of the file, try to parse the values
			try:
				pid, nz, nn, massfrac = int(columns[0]), int(columns[1]), \
					int(columns[2]), float(columns[3])
			# If values won't parse, then it's probably a header -- ignore it
			except ValueError:
				continue
			# If we haven't seen any values yet or this mass frac is smaller, save it
			if smallest is None or massfrac < smallest:
				smallest = massfrac
			# Just in case, delete the values from this line of the file
			del columns, pid, nz, nn, massfrac
	# Return whatever we found
	return smallest

def run_burn_query(hdf5, inputs):
	# Create a new subprocess to run burn_query from python, feed it the HDF5 file list
	query = subprocess.Popen([BURN_QUERY_PATH] + hdf5, stdin=subprocess.PIPE)
	# Communicate with the subprocess to send the sequence of inputs it requires
	query.communicate(inputs)

main()

