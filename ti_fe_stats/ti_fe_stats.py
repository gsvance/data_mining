#!/usr/bin/env python

# Quick script for running statistics to look at the Ti/Fe ratios from cco2
# Work out the full list of 44Ti/(Fe+56Ni) values for the cco2 particle data
# Print out a few statistics for the data set, and make a histogram too
 
# Last modified 6/30/17 by Greg Vance

# I seldom actually use Numpy on Saguaro, but it will be great for this
import numpy as np
# Use Matplotlib for histogram plotting
import matplotlib.pyplot as plt

# Giant CSV file containing all the per-particle data for the cco2 simulation
CCO2_PLOTTING_FILE = "/home/gsvance/results/plotting/cco2_plotting.out"
# Name of histogram output image
HISTOGRAM_OUTPUT = "histogram.png"
LOG_HISTOGRAM_OUTPUT = "log_histogram.png"

# Main program, called at the bottom of this file
def main():
	# Print a starting message for the user
	print "Aquiring 44Ti/(Fe+56Ni) ratio data from cco2 simulation..."
	# Read the first line of the data file to get the column headers
	with open(CCO2_PLOTTING_FILE, "r") as data_file:
		headers = data_file.readline().strip().split(", ")
	# Find which columns of the file have the numbers that we need
	col_44Ti = headers.index("A_{44Ti}")
	col_Fe = headers.index("A_{Fe}")
	col_56Ni = headers.index("A_{56Ni}")
	# Use Numpy's handy loadtxt function to read the data from file into arrays
	data_44Ti, data_Fe, data_56Ni = np.loadtxt(CCO2_PLOTTING_FILE, delimiter=", ",
		skiprows=1, usecols=(col_44Ti, col_Fe, col_56Ni), unpack=True)
	# Calculate the actual list of ratios that I want to analyze
	Ti_Fe = data_44Ti / (data_Fe + data_56Ni)
	# Remove any useless values that are either zero or NaN
	Ti_Fe = Ti_Fe[np.nonzero(Ti_Fe)]
	Ti_Fe = Ti_Fe[np.isfinite(Ti_Fe)]
	# Print the size of the usable data set
	print "\nUsable nonzero values:", Ti_Fe.size
	# Print a few of the basic ordering statistics to get sense of the range
	print "\nOrdering statistics:"
	print "          minimum:", scientific(np.amin(Ti_Fe))
	print "   5th percentile:", scientific(np.percentile(Ti_Fe, 5.))
	print "     1st quartile:", scientific(np.percentile(Ti_Fe, 25.))
	print "           median:", scientific(np.median(Ti_Fe))
	print "     3rd quartile:", scientific(np.percentile(Ti_Fe, 75.))
	print "  95th percentile:", scientific(np.percentile(Ti_Fe, 95.))
	print "          maximum:", scientific(np.amax(Ti_Fe))
	# Print a few statistics for the average and spread of the data
	print "\nAverage and spread statistics:"
	print "      mean:", scientific(np.mean(Ti_Fe))
	print "   std dev:", scientific(np.std(Ti_Fe))
	print "  variance:", scientific(np.var(Ti_Fe))
	# Make a Matplotlib histogram of the data
	print "\nMaking histogram of data..."
	plt.figure("Histogram")
	n, bins, patches = plt.hist(Ti_Fe, 100, (0.0, 0.01), facecolor="red")
	# Add labels and save the histogram to file
	plt.xlabel("44Ti / (Fe + 56Ni)")
	plt.ylabel("Bin count")
	plt.title("Titanium/Iron Ratios for cco2 Particles")
	plt.savefig(HISTOGRAM_OUTPUT, dpi=100)
	# Take the log of all data and repeat the analysis in log space
	print "\nRepeating statistical analysis in log space..."
	log_Ti_Fe = np.log10(Ti_Fe)
	# Print the same sets of statistics once again in log space
	print "\nOrdering statistics in log space:"
	print "          minimum:", rounded(np.amin(log_Ti_Fe))
	print "   5th percentile:", rounded(np.percentile(log_Ti_Fe, 5.))
	print "     1st quartile:", rounded(np.percentile(log_Ti_Fe, 25.))
	print "           median:", rounded(np.median(log_Ti_Fe))
	print "     3rd quartile:", rounded(np.percentile(log_Ti_Fe, 75.))
	print "  95th percentile:", rounded(np.percentile(log_Ti_Fe, 95.))
	print "          maximum:", rounded(np.amax(log_Ti_Fe))
	print "\nAverage and spread statistics in log space:"
	print "      mean:", rounded(np.mean(log_Ti_Fe))
	print "   std dev:", rounded(np.std(log_Ti_Fe))
	print "  variance:", rounded(np.var(log_Ti_Fe))
	# Make a Matplotlib histogram of the logged data
	print "\nMaking histogram of log space data..."
	plt.figure("Log Histogram")
	n, bins, patches = plt.hist(log_Ti_Fe, 100, (-6.0, 0.0), facecolor="blue")
	# Add labels and save the histogram to file again
	plt.xlabel("log(44Ti / (Fe + 56Ni))")
	plt.ylabel("Bin count")
	plt.title("Log of Titanium/Iron Ratios for cco2 Particles")
	plt.savefig(LOG_HISTOGRAM_OUTPUT, dpi=100)
	# Print a blank line to end
	print

# Shortcut function for printing a number in nice scientific notation
def scientific(f):
	return "%.3e" % (f)

# Shortcut function to print a nicely rounded floating point number
def rounded(f):
	return "%.3f" % (f)

main()

