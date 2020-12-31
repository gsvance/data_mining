# Python library containing many utility functions and global variables for data mining
# Most of this stuff is needed by more than one script and this keeps the code well-organized

# Last modified 31 Dec 2020 by Greg Vance

import os
import sys
import subprocess
import glob
import re
import mmap

from elements import SYMBOLS


# GLOBAL CONSTANTS

# The max value of tpos to DM process using entropy, excepting the final timestep
TPOS_MAX = 1.0
# Mass fraction threshold to use for all queries, e.g., 6 indicates 1e-6
FMASS_CUT = '6'
# Mass fraction threshold to use for isotopes needing a low cut, 1e-12
FMASS_CUT_LOW = '12'
# Isotopes that need the lower cut for various reasons
ISOTOPES_LOW = ("1n",
	"7Be", "9Be", "10Be",
	"10B", "11B",
	"12C", "13C",
	"14N", "15N",
	"16O", "17O", "18O",
	"24Mg", "25Mg", "26Mg",
	"26Al", "27Al",
	"28Si", "29Si", "30Si",
	"40K", "41K",
	"43Ca",
	"44Ti", "46Ti", "47Ti", "48Ti", "49Ti", "50Ti",
	"50Cr", "52Cr", "53Cr", "54Cr",
	"54Fe", "56Fe", "57Fe", "58Fe", "60Fe",
	"58Ni", "60Ni", "61Ni", "62Ni", "64Ni"
	"84Sr", "86Sr", "87Sr", "88Sr",
	"95Mo", "96Mo", "97Mo", "98Mo")

# Location of the file listing all isotopes to run queries on
ISOTOPES_FILE = "/home/gsvance/data_mining/isotopes.txt"
# Location of the file listing all elements and isotopes to collect for plots
ABUNDANCES_FILE = "/home/gsvance/data_mining/abundances.txt"

# DM preprocessing directories to add to the simulation head directory
PRE_DIRECTORIES = ("sbatch", "queries")
# DM postprocessing directories to add to the simulation head directory
POST_DIRECTORIES = ("analysis", "sorted_queries")

# Conversion factors for converting SNSPH quantities to CGS units
# "Exact" values taken from an initial.ctl file used by SNSPH
SNSPH_MASS = 1e-6 * 1.9889e33  # 1e-6 Msun in grams
SNSPH_LENGTH = 6.955e10  # 1 Rsun in centimeters
SNSPH_TIME = 100.0  # 100 seconds
SNSPH_VELOCITY = SNSPH_LENGTH / SNSPH_TIME
SNSPH_DENSITY = SNSPH_MASS / SNSPH_LENGTH**3
SNSPH_ACCELERATION = SNSPH_LENGTH / SNSPH_TIME**2


# FILE OPERATIONS

# Return a list of all the isotope or element names stored in a file
def get_list(filename):
	# Open up the isotopes file for reading
	iso_file = open(filename, 'r')
	# The file contains many isotopes separated by various whitespaces
	iso_list = iso_file.read().split()
	# Isotopes file is no longer needed, close it now
	iso_file.close()
	# Return the constructed list of isotopes
	return iso_list

# Given an arbitrary file name, return its extension string without the dot
def get_ext(filename):
	# Split the file name into its name and extension
	extension = os.path.splitext(filename)[1]
	# Return an empty string for no extension, otherwise drop the '.' prefix and return
	if extension == "":
		return ""
	else:
		return extension[1:]

# Given the name of an SDF file, return the float value of tpos that is declared therein
def get_tpos(filename):
	# Open the SDF file for binary reading to pass along to the memory map
	with open(filename, "rb") as sdf:
		# Create an mmap of the file for speedy reading of what we want
		sdfmm = mmap.mmap(sdf.fileno(), length=10**4, access=mmap.ACCESS_READ)
		# Use a simple regex to find the tpos line
		match = re.search(b"^float tpos = ([-+0-9.eE]+);$", sdfmm,
			re.MULTILINE)
		# Extract the numerical value from group 1 of the regex match
		if match:
			tpos = float(match.group(1))
		# Raise an error if the tpos value was not found
		else:
			raise IOError("no tpos value found in file %s" % (filename))
		# Explicitly close the map now that we're done with it
		sdfmm.close()
	# Return the tpos float value that was recovered
	return tpos

# Return names of SDF files from the SDF subdirectory that need to be DM processed in various ways
# There are four different modes in which this function can be told to operate:
#  - all: default, return a list of all SDF files that need to be DM preprocessed by entropy
#  - first: return the SDF file with the lowest tpos value (for Ye values in DM postprocessing)
#  - last: return the SDF file with the highest tpos value (for unburned yields and plotting data)
#  - early: return a list of all SDF files with tpos up to TPOS_MAX (for peak temp and rho in DM postprocessing)
# The final optional argument appends a ".out" extension to list the entropy outfiles instead
def sdf_list(paths, mode="all", dotout=False):
	# Check that the mode setting is actually one of the available options
	if mode not in ("all", "first", "last", "early"):
		raise ValueError("unknown mode setting in sdf_list: %s" % (mode))
	# Prepare to add the ".out" extension to file names if desired
	out = (".out" if dotout else "")
	# Create a list and store the names of all SDF files (they have digits for file extensions)
	sdf_files = [f for f in os.listdir(paths["sdf"]) if get_ext(f).isdigit()]
	# Change the list entries to tuples that also include the file's tpos value
	sdf_files = [(sdf, get_tpos(os.path.join(paths["sdf"], sdf))) for sdf in sdf_files]
	# Sort the list of files by their tpos values in ascending order
	sdf_files.sort(key=lambda x : x[1])
	# If only the last file was requested, return that file name by itself
	if mode == "last":
		# Send the file name without the associated tpos value
		return (sdf_files[-1][0] + out)
	# Likewise, if only the first file was requested, return that file name by itself
	if mode == "first":
		# Send the file name without its tpos value attached
		return (sdf_files[0][0] + out)
	# Otherwise, find the index of the first SDF file with tpos >= TPOS_MAX
	i = 0
	while sdf_files[i][1] < TPOS_MAX:
		i += 1
	# Select all files up to and including this one so they can be DM processed to find peak temps
	selected = sdf_files[:i+1]
	# Also run entropy on the SDF file from the final time step for use in SPH visualizations
	# Exclude this file when DM postprocessing to find the simulation's peak temperatures
	if len(sdf_files) > i + 1 and mode != "early": # mode == "all"
		selected.append(sdf_files[-1])
	# Remove all the tpos values and return the list of selected SDF files
	return [(sdf[0] + out) for sdf in selected]


# USER INTERFACE UTILITY

# Prompt the user with a question, return whether the answer was a yes
def ask_user(question):
	# Ask the user the question and indicate their two options
	response = raw_input(question + " [y/n] ").lower()
	# Return whether the answer was a yes
	return (response == "y" or response == "yes")


# DIRECTORY OPERATIONS

# Given a directory name "head" containing simulation data, return a dictionary with the following:
#     "head": full path to the specified head directory
#     "hdf5": full path to the subdirectory containing HDF5 files
#     "sdf": full path to the subdirectory containing SDF files
# Selections are manually verified with the user before being returned by the function
def get_paths(head):
	# Store the head directory name and find out its absolute path
	paths = {"head": os.path.abspath(head)}
	# Signal the user that the program is searching for the appropriate paths
	print "Searching for paths in directory: %s" % (paths["head"])
	# Prepare to store names of all directories found to have either of the desired file types
	has_hdf5, has_sdf = [], []
	# Explore all of the head dir's subdirs, try to find the ones with HDF5 and SDF files
	for subdir in os.listdir(paths["head"]):
		# Construct the full path to this subdirectory
		subdirpath = os.path.join(paths["head"], subdir)
		# Check to make sure it is actually a directory and not a file
		if not os.path.isdir(subdirpath):
			# Not a directory, skip it
			continue
		# Make a set of the unique file extensions present in this directory
		extensions = set()
		for some_file in os.listdir(subdirpath):
			extensions.add(get_ext(some_file))
		# See whether any HDF5 files are here
		if "h5" in extensions:
			# Record the directory's full path
			has_hdf5.append(subdirpath)
		# Find out if any SDF files are here
		for ext in extensions:
			# SDF files have purely numeric file extensions
			if ext.isdigit():
				# Record the directory's full path
				has_sdf.append(subdirpath)
				# Skip the rest of the extensions to avoid appending many times
				break
	# Make sure the HDF5 directory was found unambiguously
	if len(has_hdf5) == 1:
		# A single directory, everything is fine
		print "HDF5 directory: %s" % (has_hdf5[0])
		# Save the full path to that directory
		paths["hdf5"] = has_hdf5[0]
	else:
		# There was no directory, or there was more than one
		print "Failed to find HDF5 directory (%s possibilities)" % (len(has_hdf5))
	# Make sure the SDF directory was found unambiguously
	if len(has_sdf) == 1:
		# One directory, all is well
		print "SDF directory: %s" % (has_sdf[0])
		# Save the directory's full path
		paths["sdf"] = has_sdf[0]
	else:
		# No directory found, or more than one found
		print "Failed to find SDF directory (%s possibilities)" % (len(has_sdf))
	# These all need to be correct, so ask the user whether to continue execution
	if not ask_user("Continue program execution?"):
		print "Aborting on user command"
		sys.exit()
	# With user confirmation, return the paths to main() so the script can proceed
	return paths

# Given a paths dictionary as returned by get_paths, make several new subdirectories under the head
# These new directories will be added to the dictionary and the dictionary will then be returned
def make_dirs(paths, newdirs):
	# Establish counters to report what was done
	made, found = 0, 0
	# Go through each new directory name in turn
	for subdir in newdirs:
		# Construct the full path to the desired directory
		subdirpath = os.path.join(paths["head"], subdir)
		# Check whether this directory already exists
		if not os.path.exists(subdirpath):
			# If the directory does not exist, fix that and count it
			os.makedirs(subdirpath)
			made += 1
		else:
			# Directory is already here, count it
			found += 1
		# Add the full directory path to the paths variable
		paths[subdir] = subdirpath
	# Print a report message and return the new paths variable
	print "\n%s DM processing directories found, %s additional directories created" % (found, made)
	return paths

# Given a paths dictionary as returned by get_paths, check for existence of specified subdirectories
# Add those directories to the paths dictionary and return it, raise an error if they don't exist
def check_dirs(paths, dirs):
	# Loop over each directory name in turn
	for subdir in dirs:
		# Construct the full path to the sought subdirectory
		subdirpath = os.path.join(paths["head"], subdir)
		# If it exists, add it to the paths dictionary
		if os.path.exists(subdirpath):
			paths[subdir] = subdirpath
		# If it doesn't exist, raise an error about it
		else:
			raise IOError("directory '%s' being checked does not exist!" % (subdir))
	# If no errors, then return the expanded paths dictionary
	return paths


# ELEMENT UTILITIES

# Take a string specifying an elemental isotope and return the values of N and Z as strings
# Note: method for parsing the string isn't great, but it supports both formats (22Na and Na22)
#       --> it would even support the form 2N2a and read it as the same exact thing...
def nn_nz(isotope):
	# Pick out all the digits from the isotope string, this is the mass number
	mass = ''.join([x for x in isotope if x.isdigit()])
	# Pick out the letters from the isotope string, this is the element's symbol
	symbol = ''.join([x for x in isotope if x.isalpha()])
	# Find where the symbol appears in the symbols list, that index is nz
	nz = SYMBOLS.index(symbol)
	# Since mass = nn + nz, find nn using nz and the mass
	nn = int(mass) - nz
	# Convert nn and nz to strings, then return them both
	return str(nn), str(nz)

# Take the N and Z values for an isotope and return its name using isotope notation (e.g., 22Na)
def iso_name(nn, nz):
	# The atomic mass is defined as nn + nz (allow for the arguments to be strings)
	mass = str(int(nn) + int(nz))
	# Find the appropriate elemental symbol for this value of nz
	symbol = SYMBOLS[int(nz)]
	# Concatenate the two strings together to form the name of the isotope
	return (mass + symbol)


# SLURM UTILITIES

# Write and save a single standard-format sbatch script using the given string values
def write_script(scriptfile, command, stdout, stderr, walltime):
	# Start a list to store all lines that will go in the file
	lines = []
	# Start with the bash shebang and a blank line
	lines.append("#!/bin/bash\n")
	### Slurm partition option (just use the default partition)
	##lines.append("#SBATCH -p cluster")
	# Slurm cores option (only 1 is needed)
	lines.append("#SBATCH -n 1")
	# Slurm wall time option (D-HH:MM), provided as a function argument
	lines.append("#SBATCH -t " + walltime)
	# Slurm stdout file name, provided as a function argument
	lines.append("#SBATCH -o " + stdout)
	# Slurm stderr file name, also provided as a function argument
	lines.append("#SBATCH -e " + stderr)
	# Slurm mail notification option (tell me about end & fail)
	lines.append("#SBATCH --mail-type=END,FAIL")
	# Slurm email-to address (my ASU gmail address)
	lines.append("#SBATCH --mail-user=gsvance@asu.edu")
	# State the actual command that makes the script do something useful
	lines.append(command)
	# Open up the designated sbatch script file for writing
	script = open(scriptfile, 'w')
	# Write all of the lines to the file with newlines in between
	script.write('\n'.join(lines))
	# Close the file and be done with it
	script.close()
	# Print the name of the script file when finished
	print scriptfile

# Submit an sbatch script from within python, return the sbatch exit code
def sbatch(filename):
	# Construct the appropriate submit command
	command = ["sbatch", filename]
	# Print the effective shell command that is about to be run
	print ">> " + ' '.join(command)
	# Call a subprocess to submit the script with the sbatch command
	exit_code = subprocess.call(command)
	# Return the exit code that sbatch sent
	return exit_code

# Clean up all the files in a simulation's sbatch dir prior to DM postprocessing
# Delete any of the sbatch job .out or .err files that are completely empty
# Also delete any .err files that contain run_query.py overwrite errors
def sbatch_cleanup(paths):
	# Print a quick alert message to the program user
	print "\nCleaning out sbatch files in %s" % (paths["sbatch"])
	# Use glob to make lists of all the simulation's slurm .out and .err files
	out_files = glob.glob(os.path.join(paths["sbatch"], "slurm.*.*.out"))
	err_files = glob.glob(os.path.join(paths["sbatch"], "slurm.*.*.err"))
	# Loop over all of the simulation's the slurm .out and .err files
	for each_file in out_files + err_files:
		# Check if each file is empty (has zero size)
		if os.path.getsize(each_file) == 0:
			# Delete those files that are found to be empty
			os.remove(each_file)
	# Re-make the list of slurm .err files since some may have been deleted
	err_files = glob.glob(os.path.join(paths["sbatch"], "slurm.*.*.err"))
	# This string is a convenient signal for run_query.py overwrite failure
	signal = "!!! OVERWRITE FAILURE IN RUN_QUERY, BURN_QUERY WAS NOT RUN !!!"
	# Loop over each remaining slurm .err file again
	for err_file in err_files:
		# Open the file so we can look at the contents
		file_object = open(err_file, "r")
		# Read the file contents into a python string
		contents = file_object.read()
		# Close the open file, we're done with it
		file_object.close()
		# Check for the signal phrase in the contents of the file
		if contents.find(signal) != -1:
			# Delete the file if it has the phrase
			os.remove(err_file)


# SNSPH CONVERSION UTILITIES

# Given a tuple of STRING values, multiply each one of them by the factor
# Base function for all the convert utilities that follow this definition
def convert(values, factor):
	# Raise error if no values were passed at all
	if len(values) == 0:
		raise ValueError("values sequence of length zero encountered in convert")
	# If one value was passed, extract it from the tuple
	if len(values) == 1:
		return str(factor * float(values[0]));
	# If several values were passed, return another tuple
	else: # len(values) > 1
		return tuple(str(factor * float(value)) for value in values)

# Convert lengths from SNSPH units to centimeters
def convert_length(*largs):
	return convert(largs, SNSPH_LENGTH)

# Convert masses from SNSPH units to grams
def convert_mass(*margs):
	return convert(margs, SNSPH_MASS)

# Convert times from SNSPH units to seconds
def convert_time(*targs):
	return convert(targs, SNSPH_TIME)

# Convert velocities from SNSPH units to cm/s
def convert_velocity(*vargs):
	return convert(vargs, SNSPH_VELOCITY)

# Convert densities from SNSPH units to g/cm^3
def convert_density(*dargs):
	return convert(dargs, SNSPH_DENSITY)

# Convert accelerations from SNSPH units to cm/s^2
def convert_acceleration(*aargs):
	return convert(aargs, SNSPH_ACCELERATION)


