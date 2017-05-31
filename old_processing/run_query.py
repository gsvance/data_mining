#!/usr/bin/env python

# Wrapper for burn_query that takes arguments from command line for a single isotope query
# Eventually, I hope to just rewrite burn_query's interface, but this will help out for now

# Last modified 4/4/16 by Greg Vance

# Example usage:
#	./run_query.py -i 26Al -a 6 -o 26Al.out jet3b/j3b.dir/*.h5
# To search for 26Al above 1e-6 abundance in the jet3b HDF5 files
# Results will be written to a new file named Al26.out

import argparse
import os.path
import subprocess

# Full path to the compiled burn_query executable
BURN_QUERY_PATH = "/home/gsvance/data_mining/burn_query"

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
		# Raise an error and stop everything!
		raise IOError("run_query.py: specified outfile '%s' already exists!" % outfile)
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

# Take a string specifying an elemental isotope and return the values nn and nz as strings
def nn_nz(isotope):
	# List of every elemental symbol, the index corresponds to nz (nz = 0 is neutronium)
	# This is ugly coding, but it works and maybe I'll move it to another file later on
	symbols = ['n', 'H', 'He', 'Li', 'Be', 'B', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Sc', 'Ti', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Zn', 'Ga', 'Ge', 'As', 'Se', 'Br', 'Kr', 'Rb', 'Sr', 'Y', 'Zr', 'Nb', 'Mo', 'Tc', 'Ru', 'Rh', 'Pd', 'Ag', 'Cd', 'In', 'Sn', 'Sb', 'Te', 'I', 'Xe', 'Cs', 'Ba', 'La', 'Ce', 'Pr', 'Nd', 'Pm', 'Sm', 'Eu', 'Gd', 'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu', 'Hf', 'Ta', 'W', 'Re', 'Os', 'Ir', 'Pt', 'Au', 'Hg', 'Tl', 'Pb', 'Bi', 'Po', 'At', 'Rn', 'Fr', 'Ra', 'Ac', 'Th', 'Pa', 'U', 'Np', 'Pu', 'Am', 'Cm', 'Bk', 'Cf', 'Es', 'Fm', 'Md', 'No', 'Lr', 'Rf', 'Db', 'Sg', 'Bh', 'Hs', 'Mt', 'Ds', 'Rg', 'Cn', 'Uut', 'Fl', 'Uup', 'Lv', 'Uus', 'Uuo']
	# Pick out all the digits from the isotope string, this is the mass number
	mass = ''.join([x for x in isotope if x.isdigit()])
	# Pick out the letters from the isotope string, this is the element's symbol
	symbol = ''.join([x for x in isotope if x.isalpha()])
	# Find where the symbol appears in the symbols list, that index is nz
	nz = symbols.index(symbol)
	# Since mass = nn + nz, find nn using nz and the mass
	nn = int(mass) - nz
	# Convert nn and nz to strings, then return them both
	return str(nn), str(nz)

def run_burn_query(hdf5, inputs):
	# Create a new subprocess to run burn_query from python, feed it the HDF5 file list
	query = subprocess.Popen([BURN_QUERY_PATH] + hdf5, stdin=subprocess.PIPE)
	# Communicate with the subprocess to send the sequence of inputs it requires
	query.communicate(inputs)

main()

