#!/usr/bin/env python

# For each sim, report the min and max per-particle values of the following ratios and abundances:
#     40K/39K, 40K/K, K/Ca, Ca, Si, K/Si, K/Mg
# Also produce text files with complete lists of these values for histograms and scatter plots

# Last modified 11/22/16 by Greg Vance

import os

# The directory containing all of the simulation data
DATA_DIR = "/home/gsvance/sn_data/"
# Tuple of the relevant isotopes for these calculations
ISOTOPES = ("24Mg", "25Mg", "26Mg", "39K", "40K", "40Ca", "41Ca", "44Ca", "28Si", "29Si", "30Si")
# Calculated values that should be added in
CALCULATED = (("K", lambda x: x["39K"] + x["40K"]),
	("Ca", lambda x: x["40Ca"] + x["41Ca"] + x["44Ca"]),
	("Si", lambda x: x["28Si"] + x["29Si"] + x["30Si"]),
	("Mg", lambda x: x["24Mg"] + x["25Mg"] + x["26Mg"]))
# Ratios and abundances that we are interested in knowing about
RATIOS = (("40K/39K", lambda x: x["40K"] / x["39K"]),
	("40K/K", lambda x: x["40K"] / x["K"]),
	("K/Ca", lambda x: x["K"] / x["Ca"]),
	("40K/Ca", lambda x: x["40K"] / x["Ca"]),
	("Ca", lambda x: x["Ca"]),
	("Si", lambda x: x["Si"]),
	("K/Si", lambda x: x["K"] / x["Si"]),
	("K/Mg", lambda x: x["K"] / x["Mg"]))

def main():
	# Loop over all the simulations and carry out the appropriate calculations for each
	for sim in sorted(os.listdir(DATA_DIR)):
		# Print the simulation name for the user's convenience
		print "%s:" % (sim)
		# Read in and organize all of the available data for this simulation
		data = get_data(sim)
		# Add in the calculated total values for both K and Ca
		data = add_calculated(data)
		# Make dictionaries of every obtainable value for the desired ratios
		ratios = get_ratios(data)
		# Nicely print out the minimum and maximum for each ratio
		output_minmax(ratios)
		# Write the ratio dictionaries to files so histograms can be made
		write_files(sim, ratios)

# Read in all of the data from the needed files and organize it by particle in a dictionary
def get_data(sim):
	# Establish the location of the data files
	location = os.path.join(DATA_DIR, sim, "sorted_queries")
	# Set up the data dictionary and loop over isotopes to fill it
	data = {}
	for isotope in ISOTOPES:
		# Read the contents of the isotope's file
		contents = read_file(os.path.join(location, isotope + ".out"))
		# Add everything to the data dictionary
		for line in contents:
			if line[0] not in data:
				data[line[0]] = {}
			data[line[0]][isotope] = line[1]
	# Go back and check for missing values, set them to zero
	for pid in data.keys():
		for isotope in ISOTOPES:
			if isotope not in data[pid]:
				data[pid][isotope] = 0.
	# Return the dictionary of data
	return data

# Read the contents of one file into a helpful list of tuples
def read_file(filename):
	# Make an empty list to store the file contents
	contents = []
	# Open the file and skip its first line (the header)
	myfile = open(filename, "r")
	myfile.readline()
	# Loop over the file lines and extract the particle ID and abundance
	for line in myfile:
		# Split the line up -- 1st is the particle ID and 4th is the abundance
		splitline = line.strip().split(',')
		pid = int(splitline[0])
		abun = float(splitline[3])
		# Add a data tuple to the contents list and move on
		contents.append((pid, abun))
	# Close the file and return the list of contents
	myfile.close()
	return contents

# Add some calcuated total values to the data dictionary
def add_calculated(data):
	# Loop over every particle and add the calculated values in
	for pid in data.keys():
		for name, formula in CALCULATED:
			data[pid][name] = formula(data[pid])
	# Return the result
	return data

# Return dictionaries of all obtainable desired ratio values for this simulation's data
def get_ratios(data):
	# Make a dictionary to store the ratio dictionaries and initialize them all
	ratios = {}
	for name, formula in RATIOS:
		ratios[name] = {}
	# Try every particle to see if the ratio values are obtainable
	for pid in data.keys():
		for name, formula in RATIOS:
			try:
				ratio = formula(data[pid])
			except ZeroDivisionError:
				continue
			if ratio == 0. or (name == "40K/K" and ratio == 1.):
				continue
			# Success! Add the value to the appropriate dictionary
			ratios[name][pid] = ratio
	# Return the resulting dictionaries of values
	return ratios

# Output all of the ratios' minima and maxima in a simple format
def output_minmax(ratios):
	for name, formula in RATIOS:
		values = ratios[name].values()
		print "    %s: [%.5e, %.5e] (n = %d)" % (name, min(values), max(values), len(values))

# Write the dictionaries of ratios out to files for making histograms
def write_files(sim, ratios):
	# Write each ratio dictionary to its own unique ASCII file
	for name, formula in RATIOS:
		# Generate the file name in a standard way
		fname = "lists/" + sim + '.' + name.replace('/', '_') + ".txt"
		# Write out the key-value pairs with commas and newline separators
		with open(fname, "w") as outfile:
			output = sorted(ratios[name].items(), key=lambda x : x[0])
			outfile.write("#PID,%s\n" % (name))
			outfile.write('\n'.join(["%d,%.15e" % (pair) for pair in output]))

main()
