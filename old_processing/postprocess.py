#!/usr/bin/env python

# Complete the analysis for all data obtained from one supernova simulation
# Identify all of the directories and such, then set up postprocessing directories
# 
# (describe query sorting, yields, abundances, peak temps...)
# 

# Last edited 4/19/16 by Greg Vance

# Usage example:
#	./postprocess.py sn_data/jet3b
# To postprocess all data in the jet3b simulation directory  

import sys
import os

# Postprocessing directories to add to the simulation directory
NEW_DIRECTORIES = ["analysis", "sorted_queries"]
# The maximum value of tpos to search for peak explosion temperatures
TPOS_MAX = 1.0

def main():
	# Get all the preliminary info like directories and which isotopes to query
	paths = get_paths()
	# Make any directories that need to be made before processing begins
	paths = make_dirs(paths)
	# Generate sbatch scripts for each isotope query and place them in the right spot
	write_burn_query_scripts(paths, isotopes)
	# Determine which SDF files to process based on tpos values, make sbatch scripts for them too
	write_entropy_scripts(paths)
	# Submit all of the sbatch scripts to the saguaro cluster via slurm
	sbatch_submit(paths)
	# Print that the script has completed
	print "\nAll done!"

def get_paths():
	# This script takes exactly one argument (the head directory for the data)
	if len(sys.argv) != 2:
		# You did it wrong, try that again
		print "usage: %s [head directory]" % (sys.argv[0])
		sys.exit(1)
	# Store the argument given as the head directory for all data paths
	paths = {"head" : os.path.abspath(sys.argv[1])}
	# Signal the user that the preprocessing has begun
	print "Preprocessing directory: %s" % (paths["head"])
	# Store the names of all directories found to have each of the two file types
	hdf5, sdf = [], []
	# Explore all of the head dir's subdirs, try to find the ones with HDF5 and SDF files
	for dir in os.listdir(paths["head"]):
		# Construct the full path to the subdirectory
		dirpath = os.path.join(paths["head"], dir)
		# Check to make sure it is actually a directory and not a file
		if not os.path.isdir(dirpath):
			# Not a directory, skip it
			continue
		# Make a list of the file extensions present in this directory
		extensions = []
		for some_file in os.listdir(dirpath):
			extensions.append(get_ext(some_file))
		# See whether any HDF5 files are here
		if "h5" in extensions:
			# Record the directory's full path
			hdf5.append(dirpath)
		# Find out if any SDF files are here
		for ext in extensions:
			# SDF files have purely numeric file extensions
			if ext.isdigit():
				# Record the directory's full path
				sdf.append(dirpath)
				# Skip the rest of the extensions to avoid appending many times
				break
	# Make sure the HDF5 directory was found unambiguously
	if len(hdf5) == 1:
		# A single directory, everything is fine
		print "\nHDF5 directory: %s" % (hdf5[0])
		# Save the full path to that directory
		paths["hdf5"] = hdf5[0]
	else:
		# There was no directory, or there was more than one
		print "\nFailed to find HDF5 directory (%s possibilities)" % (len(hdf5))
	# Ask user whether to continue execution, abort if no
	response = raw_input("Continue script execution? [y/n] ")
	if response.lower() != 'y':
		print "Aborting on user command"
		sys.exit()
	# Make sure the SDF directory was found unambiguously
	if len(sdf) == 1:
		# One directory, all is well
		print "\nSDF directory: %s" % (sdf[0])
		# Save the directory's full path
		paths["sdf"] = sdf[0]
	else:
		# No directory found, or more than one found
		print "\nFailed to find SDF directory (%s possibilities)" % (len(sdf))
	# Ask user again whether to continue execution or abort
	response = raw_input("Continue script execution? [y/n] ")
	if response.lower() != 'y':
		print "Aborting on user command"
		sys.exit()
	# With user confirmation, return the paths to main() so the script can proceed
	return paths

def make_dirs(paths):
	# Go through each required preprocessing directory
	for dir in NEW_DIRECTORIES:
		# Construct the full path to the desired directory
		dirpath = os.path.join(paths["head"], dir)
		# Check whether this directory already exists
		if not os.path.exists(dirpath):
			# If the directory does not exist, fix that
			os.makedirs(dirpath)
		# Add the full directory path to the paths variable
		paths[dir] = dirpath
	# Print a progress message and return the new paths variable
	print "\nPreprocessing directories checked"
	return paths

