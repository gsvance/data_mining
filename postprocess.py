#!/usr/bin/env python

# Complete the analysis for all data obtained from one supernova simulation
# Identify all of the directories and such, then set up postprocessing directories
# Look through all the slurm .out files and extract the simulation's total yields
# Update the extracted total yields using the unburned yields from the SDF files
# Sort the outfiles from burn_query because their contents start out disorganized
# Combine all of the desired plotting values into a single file, including:
#   - Particle IDs, final positions, masses, smoothing lengths
#   - Particle densities at the final timestep (plot)
#   - Peak explosion temperatures for each particle (plot)
#   - Selected elemental abundances for each particle (plot)

# Last edited 11/13/17 by Greg Vance

# Usage example:
#	./postprocess.py sn_data/jet3b
# To postprocess all data in the jet3b simulation directory 

import sys
import os
import subprocess
import collections
import glob

import sn_utils as sn
from particler import Particler

# Full path to the extract_yields.sh executable shell script
EXTRACT_YIELDS_PATH = "/home/gsvance/data_mining/extract_yields.sh"
# Full path to the compiled update_yields executable
UPDATE_YIELDS_PATH = "/home/gsvance/data_mining/update_yields"
# Full path to the sort_query.sh executable shell script
SORT_QUERY_PATH = "/home/gsvance/data_mining/sort_query.sh"

# Main program for postprocessing, called at the end of this file
def main():
	# Start by checking the number of arguments passed to the script
	if len(sys.argv) != 2:
		# There should only be one argument!
		print "Usage: %s simulation_directory" % (sys.argv[0])
		sys.exit(1)
	# Look in the simulation directory and identify all the raw data directories
	paths = sn.get_paths(sys.argv[1])
	# Check that the required preprocessing subdirectories already exist
	paths = sn.check_dirs(paths, sn.PRE_DIRECTORIES)
	# Make any new directories that need to be made before processing continues
	paths = sn.make_dirs(paths, sn.POST_DIRECTORIES)
	# Clean out extraneous sbatch output files before we do anything else
	sn.sbatch_cleanup(paths)
	# Extract the simulation's total yields and put them in the correct file
	extract_yields(paths)
	# Update the simulation's total yields with unburned data and save that too
	update_yields(paths)
	# Sort the burn_query output files and put them all in the right directory
	sort_queries(paths)
	# Read in the abundances file, which specififes the elements to eventually plot
	abundances = sn.get_list(sn.ABUNDANCES_FILE)
	# Assemble the extensive ASCII file of the various particle plotting values
	write_particles(paths, abundances)
	# Print a final status message when the program completes
	print "\nFinished!"

# Run extract_yields.sh to create the simulation's total yields file
def extract_yields(paths):
	# Print a progress indicator message
	print "\nExtracting total simulation yields"
	# Look up the path to the preprocessing sbatch directory
	sbatch_dir = paths["sbatch"]
	# Get the name that's on the head simulation directory
	simname = os.path.basename(paths["head"])
	# Construct the full path to the new total yields file
	yields = "%s_yields.out" % (simname)
	yields_path = os.path.join(paths["analysis"], yields)
	# Assemble the appropriate shell command to be executed
	command = [EXTRACT_YIELDS_PATH, sbatch_dir, yields_path]
	# Print the command to screen just before executing it
	print ">> " + ' '.join(command)
	# Call a subprocess to execute the shell script from within Python
	subprocess.call(command)
	# Let user inspect output from the command and ask before continuing
	if not sn.ask_user("Continue program execution?"):
		print "Aborting on user command"
		sys.exit()

# Run the update_yields program to create an updated yields file for the simulation
def update_yields(paths):
	# Make sure the simulation has SDF files before trying to use SDF data
	# Also skip this if we somehow have no HDF5 data to use in the first place
	if "sdf" not in paths or "hdf5" not in paths:
		# Skip this function if no files exist
		return
	# Print a quick progress message for the user
	print "\nUpdating total yields with unburned yields data"
	# Use glob to match the name of the unburned yields SDF file
	unburned_glob = glob.glob(os.path.join(paths["sdf"], "*.unburned.out"))
	# Be sure that EXACTLY one file matches the unburned yields name format
	if len(unburned_glob) != 1:
		print "Error: matched %d .unburned.out files" % (len(unburned_glob))
		sys.exit()
	# Save the full path to the unburned yields SDF file
	unburned_path = unburned_glob[0]
	# Get the simulation name from the head directory
	simname = os.path.basename(paths["head"])
	# Construct the full path to the simulation's total yields file
	yields = "%s_yields.out" % (simname)
	yields_path = os.path.join(paths["analysis"], yields)
	# Construct the full path to the particle IDs file
	pids_path = os.path.join(paths["hdf5"], simname + "_pids.out")
	# Assemble the full shell command to run the executable
	command = [UPDATE_YIELDS_PATH, yields_path, unburned_path, pids_path]
	# Print the command on screen before it is executed
	print ">> " + ' '.join(command)
	# Call a subprocess to execute the program from within Python
	subprocess.call(command)
	# Let the user decide whether we should continue at this point
	if not sn.ask_user("Continue program execution?"):
		print "Aborting on user command"
		sys.exit()

# Run sort_query.sh on each burn_query output file to prepare them for analysis
def sort_queries(paths):
	# Print a progress message to the user
	print "\nSorting all isotope query files"
	# Run the script once for each existing query file
	for query in os.listdir(paths["queries"]):
		# Construct the path to the query file
		query_path = os.path.join(paths["queries"], query)
		# Construct the path to the new sorted output file
		new_path = os.path.join(paths["sorted_queries"], query)
		# Generate the shell command needed to do the sorting
		command = [SORT_QUERY_PATH, query_path, new_path]
		# Print the command as it is being executed
		print ">> " + ' '.join(command)
		# Run the command using a python subprocess to call the script
		subprocess.call(command)
	# Allow user to inspect all output and ask before proceeding farther
	if not sn.ask_user("Continue program execution?"):
		print "Aborting on user command"
		sys.exit()

# Generate the ASCII file of particle plotting values for this simulation's data
def write_particles(paths, abundances):
	# Make sure that this simulation actually has SDF files
	if "sdf" not in paths:
		# Skip this whole function if it doesn't
		return
	# Print a quick progress message for the user
	print "\nCompiling simulation plotting values"
	# Open all of the entropy output files from the preprocessing
	# The file from the final timestep is used for SPH plotting values
	# The files from early timesteps are used to find the peak temps and rhos
	entropy_initial, entropy_final, entropy_early = entropy_files(paths)
	# Open the sorted burn_query output files organzied by the target element or isotope
	abuns_files = query_files_dict(paths, abundances)
	# Open the CSV file for writing the plotting values, name it after the simulation
	simname = os.path.basename(paths["head"])
	outname = os.path.join(paths["analysis"], "%s_plotting.out" % (simname))
	outfile = open(outname, 'w')
	# Generate a header for the output file and the content of the columns file
	header = ["id", "x", "y", "z", "vx", "vy", "vz", "mass", "h", "density", "peak temp", "peak density", "Y_{e}"]
	for abun in abundances:
		header.append("A_{%s}" % (abun))
	outfile.write(", ".join(header) + '\n')
	with open(os.path.join(paths["analysis"], "columns"), 'w') as columns:
		columns.write('\n'.join(header) + '\n')
	# Loop for every particle ID in the final time step file
	id, goal_id = 0, 0
	while not entropy_final.is_empty():
		# Print an incremental progress message based on the current ID
		if id >= goal_id:
			if id > 0:
				print "Compiling values for particle ID %s,000" % (id / 1000)
			goal_id += 50 * 1000
		# Extract the information from this line of the final time step file
		line = entropy_final.get_next(id)
		if line == []:
			# Missing ID in entropy file?
			print "Warning: particle ID %s missing from final entropy outfile" % (id)
			id += 1
			continue
		sid, x, y, z, temp, u, udot, density, vx, vy, vz, h, mass, ye_final = line
		# Determine the peak temperature and density for this particle ID
		peak_temp, peak_rho = get_peaks(id, entropy_early)
		# Determine the progenitor electron fraction for this particle ID
		ye = get_efrac(id, entropy_initial)
		# Convert everything with mass, length, or time units from SNSPH units to CGS
		x, y, z, h = sn.convert_length(x, y, z, h)
		vx, vy, vz = sn.convert_velocity(vx, vy, vz)
		mass = sn.convert_mass(mass)
		density, peak_rho = sn.convert_density(density, peak_rho)
		# Determine the abundance of each element in question at this particle ID
		abun = get_abuns(id, abuns_files)
		# Combine everything into a line that gets written to the file
		outline = [sid, x, y, z, vx, vy, vz, mass, h, density, peak_temp, peak_rho, ye]
		outline.extend(abun)
		outfile.write(", ".join(outline) + '\n')
		# Increment the particle ID
		id += 1
	# Close the final time step file and the initial timestep file
	entropy_final.close()
	entropy_initial.close()
	# Close all of the early entropy files
	for early in entropy_early:
		early.close()
	# Close all the burn_query files
	for file_list in abuns_files.values():
		for query in file_list:
			query.close()
	# Close the output CSV file
	outfile.close()

# Open the entropy outfiles, return the first one, last one, and a list of the early ones
def entropy_files(paths):
	# Get the name of the first entropy file
	first = sn.sdf_list(paths, mode="first", dotout=True)
	# Get the name of the last entropy file
	last = sn.sdf_list(paths, mode="last", dotout=True)
	# Get the names of the early entropy files
	earlies = sn.sdf_list(paths, mode="early", dotout=True)
	# Open all the files and return them
	first_part = Particler(os.path.join(paths["sdf"], first))
	last_part = Particler(os.path.join(paths["sdf"], last))
	early_parts = [Particler(os.path.join(paths["sdf"], early)) for early in earlies]
	return (first_part, last_part, early_parts)

# Open the needed query files, organized in an ordered dictionary by abundance target
def query_files_dict(paths, abundances):
	# Establish an ordered dictionary to store the name of each abundance target
	# The dictionary values are the lists of files needed for each target
	abuns_dict = collections.OrderedDict()
	# Add each abundance target and find/open the needed files
	for target in abundances:
		# See if the target is just an element
		if target.isalpha():
			# Find all relevant files
			expand = "[0-9][0-9]%s.out" % (target)
			file_list = glob.glob(os.path.join(paths["sorted_queries"], expand))
		# It must be an isotope
		else:
			expand = os.path.join(paths["sorted_queries"], "*%s.out" % (target))
			file_list = glob.glob(expand)
		# Check that something was found
		if len(file_list) == 0:
			print "Error: no query files for abundance target '%s'" % (target)
			sys.exit()
		# Add it to the dictionary
		abuns_dict[target] = [Particler(myfile) for myfile in file_list]
	# Return the dictionary
	return abuns_dict

# Retrieve the peak temperature for a particle ID from the early entropy outfiles
# Also return the particle's density at the time that the peak temperature occurred
def get_peaks(id, entropy_early):
	# Make a list to store the temperatures and densities
	temp_rho_list = []
	# Get the temp and rho from each file
	for early in entropy_early:
		# Get line from the file
		line = early.get_next(id)
		# Check which columns of the file have the temperature and density
		temp_col = early.find_column("Temp")
		rho_col = early.find_column("rho")
		# Get the temperature and density values
		temp = float(line[temp_col])
		rho = float(line[rho_col])
		# Save the (temp, rho) pair together
		temp_rho_list.append((temp, rho))
	# Find the (temp, rho) pair that had the peak temperature
	peak = max(temp_rho_list, key=lambda x : x[0])
	# Return the peak temp and rho as a pair of strings
	return str(peak[0]), str(peak[1])

# Get the progenitor (first entropy file) electron fraction Ye for the given particle ID
def get_efrac(id, entropy_initial):
	# Get the line from the progenitor entropy file
	line = entropy_initial.get_next(id)
	# Check which column has the Ye value and extract it
	col = entropy_initial.find_column("Y_e")
	ye = line[col]
	# Return the value of Ye that was extracted
	return ye

# Retrieve total abundances for a particle ID from the appropriate query files
def get_abuns(id, abuns_files):
	# Make a list to store the abundances
	abun_list = []
	# Loop for every target and find the abundances
	for target, file_list in abuns_files.items():
		# Store the abundances for summing
		abuns = []
		for myfile in file_list:
			# Get a line
			line = myfile.get_next(id)
			# If there was a line, convert value to float and save it
			if line == []:
				continue
			else:
				abuns.append(float(line[3]))
		# Add everything up and save it
		total_abun = str(float(sum(abuns)))
		abun_list.append(total_abun)
	# Return the list when done
	return abun_list

main()

