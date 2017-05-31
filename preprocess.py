#!/usr/bin/env python

# Begin the analysis for all data obtained from one supernova simulation
# Identify all of the directories, then set up the preprocessing directories
# Generate the appropriate sbatch scripts for all burn_query and entropy runs
# Finish by submitting those scripts to the saguaro cluster for execution

# Last edited 3/23/17 by Greg Vance

# Usage example:
#	./preprocess.py sn_data/jet3b
# To preprocess all data in the jet3b simulation directory  

import sys
import os

import sn_utils as sn


# Full path to the executable run_query.py script for running burn_query
RUN_QUERY_PATH = "/home/gsvance/data_mining/run_query.py"
# Full path to the compiled entropy executable file
ENTROPY_PATH = "/home/gsvance/data_mining/entropy"
# Full path to the compiled SDF Reader executable for cco2
CCO2SDF_PATH = "/home/gsvance/data_mining/cco2-SDF-reader"

# Main program for preprocessing (called at end of this file)
def main():
	# This script takes exactly one argument (the head directory for the simulation data)
	if len(sys.argv) != 2:
		# You did it wrong, try that again
		print "Usage: %s simulation_directory" % (sys.argv[0])
		sys.exit(1)
	# Get all the preliminary info like directories and which isotopes to query
	paths, isotopes = sn.get_paths(sys.argv[1]), sn.get_list(sn.ISOTOPES_FILE)
	# Make any directories that need to be made before processing begins
	paths = sn.make_dirs(paths, sn.PRE_DIRECTORIES)
	# Generate sbatch scripts for each isotope query and place them in the right spot
	write_burn_query_scripts(paths, isotopes)
	# Determine which SDF files to process based on tpos values, make sbatch scripts for them too
	write_entropy_scripts(paths)
	# Submit all of the sbatch scripts to the saguaro cluster via slurm
	sbatch_submit(paths)
	# Print that the script has completed
	print "\nAll done!"

# Write all of the needed sbatch scripts for running burn_query
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
		# Create the name of the sbatch script file to be written
		scriptfile = os.path.join(paths["sbatch"], "ISO" + iso + ".sh")
		# Name the burn_query outfile and construct the full path to it
		outfile = os.path.join(paths["queries"], iso + ".out")
		# Construct a wild card expression that will expand to the list of HDF5 file names
		hdf5_list = os.path.join(paths["hdf5"], "*.h5")
		# Check for the fabulously non-abundant isotope 40K and set the abundance threshold accordingly
		fmass_cut = (sn.FMASS_CUT_LOW if isotope in sn.ISOTOPES_LOW else sn.FMASS_CUT)
		# Put together the full run_query command that needs to be submitted
		command = "\n%s -i %s -a %s -o %s %s\n" % (RUN_QUERY_PATH, isotope, fmass_cut, outfile, hdf5_list)
		# Assemble the slurm stdout file name (in sbatch directory using the job id)
		stdout = os.path.join(paths["sbatch"], "slurm.%j.ISO" + iso + ".out")
		# Assemble the slurm stderr file name in the same way
		stderr = os.path.join(paths["sbatch"], "slurm.%j.ISO" + iso + ".err")
		# Set the script time limit to 4 hours (burn_query has taken 2+ hours before)
		walltime = "0-04:00"
		# Write the sbatch script using all these parameters
		sn.write_script(scriptfile, command, stdout, stderr, walltime)

# Write all of the needed sbatch scripts for running entropy
def write_entropy_scripts(paths):
	# Make sure there is a directory of SDF files
	if "sdf" not in paths:
		# Skip entropy scripts if no SDF dir
		return
	# Print a progress indicator message
	print "\nGenerating sbatch scripts for entropy"
	# Determine the name of the simulation so the correct reader can be used
	simname = os.path.basename(paths["head"])
	# Make sure the alternate SDF Reader is used for the cco2 simulation
	reader = CCO2SDF_PATH if simname == "cco2" else ENTROPY_PATH
	# Figure out which SDF files need to be processed and make an sbatch script for each one
	for sdf in sn.sdf_list(paths):
		# Extract the file's numeric file extension
		ext = sn.get_ext(sdf)
		# Create the name of the sbatch script file to be written
		scriptfile = os.path.join(paths["sbatch"], "SDF" + ext + ".sh")
		# Construct the full path to the SDF file to be processed
		sdf_file = os.path.join(paths["sdf"], sdf)
		# Put together the appropriate entropy command
		command = "\n%s %s\n" % (reader, sdf_file)
		# Assemble the slurm stdout file name (in sbatch dir using job id)
		stdout = os.path.join(paths["sbatch"], "slurm.%j.SDF" + ext + ".out")
		# Assemble the slurm stderr file name in the same way
		stderr = os.path.join(paths["sbatch"], "slurm.%j.SDF" + ext + ".err")
		# Set the script time limit to 1 hour (entropy runs quickly)
		walltime = "0-01:00"
		# Write the sbatch script using all these parameters
		sn.write_script(scriptfile, command, stdout, stderr, walltime)

# Submit all of the written sbatch scripts to the cluster for execution
def sbatch_submit(paths):
	# Print a progress indicator at this point
	print "\nSubmitting sbatch scripts to the cluster"
	# Determine whether to submit burn_query scripts to the cluster
	if "hdf5" in paths:
		# Do not use supercomputer time without the user's consent
		burn_query = sn.ask_user("Proceed with submitting burn_query scripts?")
	else:
		# No scripts, so nothing to submit
		burn_query = False
	# Determine whether to submit entropy scripts to the cluster
	if "sdf" in paths:
		# Do not use supercomputer time without the user's consent
		entropy = sn.ask_user("Proceed with submitting entropy scripts?")
	else:
		# No scripts, so nothing to submit
		entropy = False
	# Submit each authorized sbatch script to the cluster for execution, they are the files with .sh extensions
	for script in [f for f in os.listdir(paths["sbatch"]) if sn.get_ext(f) == "sh"]:
		# Should this script be submitted to the cluster?
		submit = False
		# Determine if this is a burn_query script or an entropy script
		if script[:3] == "ISO":
			# This is a burn_query script
			submit = burn_query
		elif script[:3] == "SDF":
			# This is an entropy script
			submit = entropy
		# If approved, proceed with submitting the script
		if submit:
			# Submit the file through sbatch
			sn.sbatch(os.path.join(paths["sbatch"], script))

main()

