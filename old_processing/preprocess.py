#!/usr/bin/env python

# Begin the analysis for all data obtained from one supernova simulation
# Identify all of the directories and such, then set up processing directories
# Generate the appropriate sbatch scripts for burn_query and entropy runs
# Finish by submitting all scripts to the saguaro cluster for execution

# Last edited 4/19/16 by Greg Vance

# Usage example:
#	./preprocess.py sn_data/jet3b
# To preprocess all data in the jet3b simulation directory  

import sys
import os
import subprocess

# Location of the file listing all isotopes to run queries on
ISOTOPES_FILE = "/home/gsvance/data_mining/isotopes.txt"
# Preprocessing directories to add to the simulation directory
NEW_DIRECTORIES = ["sbatch", "queries"]
# Full path to the executable run_query.py script for running burn_query
RUN_QUERY_PATH = "/home/gsvance/data_mining/run_query.py"
# Mass fraction threshold to use for all queries, e.g., 6 means 1e-6
ABUNDANCE = '6'
# The maximum value of tpos to process using entropy, excepting the final timestep
TPOS_MAX = 1.0
# Full path to the compiled entropy executable
ENTROPY_PATH = "/home/gsvance/data_mining/entropy"

def main():
	# Get all the preliminary info like directories and which isotopes to query
	paths, isotopes = get_paths(), get_isotopes()
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

def get_isotopes():
	# Open up the isotopes file for reading
	iso_file = open(ISOTOPES_FILE, 'r')
	# The file contains many iostopes, separated by various whitespaces
	iso_list = iso_file.read().split()
	# Isotopes file is no longer needed, close it now
	iso_file.close()
	# Print a message and return the list of isotopes to main()
	print "\nIsotopes file read"
	return iso_list

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

def write_burn_query_scripts(paths, isotopes):
	# Make sure there is a directory of HDF5 files
	if "hdf5" not in paths:
		# Skip burn_query scripts if no HDF5 dir
		return
	# Print a progress indicator message
	print "\nGenerating sbatch scripts for burn_query"
	# Make one script for each isotope query so that all queries can be run in parallel
	for isotope in isotopes:
		# Pad the isotope string with a zero out front if the mass is only one digit
		if isotope[1].isalpha():
			iso = '0' + isotope
		else:
			iso = isotope
		# Assemble slurm stdout file name (in sbatch dir using job id)
		stdout = os.path.join(paths["sbatch"], "slurm.%j.ISO" + iso + ".out")
		# Assemble slurm stderr file name in the same way
		stderr = os.path.join(paths["sbatch"], "slurm.%j.ISO" + iso + ".err")
		# Name the burn_query outfile and construct the full path to it
		outfile = os.path.join(paths["queries"], iso + ".out")
		# Construct a wild card expression that will expand to the list of HDF5 file names
		hdf5_list = os.path.join(paths["hdf5"], "*.h5")
		# Put together the full run_query command that needs to be run
		command = "\n%s -i %s -a %s -o %s %s\n" % (RUN_QUERY_PATH, isotope, ABUNDANCE, outfile, hdf5_list)
		# Create the name of the sbatch script file to be written
		scriptfile = os.path.join(paths["sbatch"], "ISO" + iso + ".sh")
		# Write the sbatch script using all these parameters
		write_script(stdout, stderr, command, scriptfile)

def write_entropy_scripts(paths):
	# Make sure there is a directory of SDF files
	if "sdf" not in paths:
		# Skip entropy scripts if no SDF dir
		return
	# Print a progress indicator message
	print "\nGenerating sbatch scripts for entropy"
	# Figure out which SDF files need to be processed and make an sbatch script for each one
	for sdf in sdf_list(paths):
		# Extract the file's numeric file extension
		ext = get_ext(sdf)
		# Assemble the slurm stdout file name (in sbatch dir using job id)
		stdout = os.path.join(paths["sbatch"], "slurm.%j.SDF" + ext + ".out")
		# Assemble the slurm stderr file name in the same way
		stderr = os.path.join(paths["sbatch"], "slurm.%j.SDF" + ext + ".err")
		# Construct the full path to the SDF file to be processed
		sdf_file = os.path.join(paths["sdf"], sdf)
		# Put together the appropriate entropy command
		command = "\n%s %s\n" % (ENTROPY_PATH, sdf_file)
		# Create the name of the sbatch script file to be written
		scriptfile = os.path.join(paths["sbatch"], "SDF" + ext + ".sh")
		# Write the sbatch script using all these parameters
		write_script(stdout, stderr, command, scriptfile)

# Given an arbitrary file name, return the extension string without the '.'
def get_ext(filename):
	# Split the file name into its name and extension
	extension = os.path.splitext(filename)[1]
	# Return an empty string for no extension, otherwise drop the '.' prefix and return
	if extension == '':
		return extension
	else:
		return extension[1:]

# Write a single standard-format sbatch script using the specified string values
def write_script(stdout, stderr, command, scriptfile):
	# Make a list to store all lines that will go in the file
	lines = []
	# Start with the bash shebang line
	lines.append("#!/bin/bash\n")
	# Slurm partition option (use the default partition)
	lines.append("#SBATCH -p cluster")
	# Slurm cores option (only 1 is needed)
	lines.append("#SBATCH -n 1")
	# Slurm wall time option (5 hours max)
	lines.append("#SBATCH -t 0-05:00")
	# Slurm stdout file name, provided as a function argument
	lines.append("#SBATCH -o " + stdout)
	# Slurm stderr file name, also provided as a function argument
	lines.append("#SBATCH -e " + stderr)
	# Slurm mail notification option (tell me about end & fail)
	lines.append("#SBATCH --mail-type=END,FAIL")
	# Slurm email-to address (my ASU gmail address)
	lines.append("#SBATCH --mail-user=gsvance@asu.edu")
	# Include the actual command argument that makes the script do something useful
	lines.append(command)
	# Open up the designated sbatch script file for writing
	script = open(scriptfile, 'w')
	# Write all of the lines to the file with newlines
	script.write('\n'.join(lines))
	# Close the file and be done with it
	script.close()
	# Print the name of the script file when finished
	print scriptfile

# Return the names of all SDF files in the SDF dir that need to be run through entropy
def sdf_list(paths):
	# Create a list and store the names of all SDF files (they have digits for file extensions)
	sdf_files = [f for f in os.listdir(paths["sdf"]) if get_ext(f).isdigit()]
	# Change the list entries to tuples that also include the file's tpos value
	sdf_files = [(sdf, get_tpos(os.path.join(paths["sdf"], sdf))) for sdf in sdf_files]
	# Sort the list of files by their tpos values in ascending order
	sdf_files.sort(key=lambda x : x[1])
	# Find the index of the first SDF file with tpos >= TPOS_MAX
	i = 0
	while sdf_files[i][1] < TPOS_MAX:
		i += 1
	# Select all files up to and including this one so they can be processed to find peak temps
	selected = sdf_files[:i+1]
	# Also process the one SDF file from the final time step for use in SPH visualizations
	if len(sdf_files) > i + 1:
		selected.append(sdf_files[-1])
	# Remove all the tpos values and return the list of selected SDF files
	return [sdf[0] for sdf in selected]

# Given the name of an SDF file, return the float value of tpos declared therein
def get_tpos(filename):
	# Open the SDF file (in non-binary mode) to look for tpos value in plain text header
	sdf = open(filename, 'r')
	# Loop through lines until the correct line is found
	found = False
	for line in sdf:
		# Check if the beginning of the line looks like a tpos declaration
		if len(line) > 13 and line[:13] == "float tpos = ":
			# Extract the numerical value between " = " and ";\n"
			tpos = float(line[line.index('=') + 2 : line.index(';')])
			# The tpos value was found, flag it and break the loop
			found = True
			break
	# Close the open SDF file, all done with it
	sdf.close()
	# Raise an error if the tpos value was not found
	if not found:
		print "error: no tpos value found for file %s" % (filename)
		sys.exit(2)
	# Return the tpos float value that was recovered
	return tpos

def sbatch_submit(paths):
	# Print a progress indicator at this point
	print "\nSubmitting sbatch scripts to the cluster"
	# Determine whether to submit burn_query scripts to the cluster
	if "hdf5" in paths:
		# Do not use supercomputer time without the user's consent
		response = raw_input("Proceed with submitting burn_query scripts? [y/n] ")
	else:
		# No scripts, so nothing to submit
		response = 'n'
	# Submit the scripts only if the user's answer was yes
	burn_query = (response == 'y')
	# Determine whether to submit entropy scripts to the cluster
	if "sdf" in paths:
		# Do not use supercomputer time without the user's consent
		response = raw_input("Proceed with submitting entropy scripts? [y/n] ")
	else:
		# No scripts, so nothing to submit
		response = 'n'
	# Submit the scripts only if the user's answer was yes
	entropy = (response == 'y')
	# Submit each authorized sbatch script to the cluster for execution, they are the files with .sh extensions
	for script in [f for f in os.listdir(paths["sbatch"]) if get_ext(f) == "sh"]:
		# Should this script be submitted to the cluster?
		submit = False
		# Determine if this is a burn_query script or an entropy script
		if script[:3] == "ISO":
			# This is a burn_query script
			submit = burn_query
		elif script[:3] == "SDF":
			# This is an entropy script
			submit = entropy
		# If approved, proceed with sumitting the script
		if submit:
			# Construct the appropriate submit command
			command = ["sbatch", os.path.join(paths["sbatch"], script)]
			# Call a subprocess to submit the script with the sbatch command
			print ' '.join(command)
			subprocess.call(command)

main()

