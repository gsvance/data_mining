#!/usr/bin/env python

# Quick script for running statistics to look at the Fe/Ti ratios from cco2
# We are interested in comparing them to the Cas A observations by Grefenstette
# Work out the full list of (Fe+56Ni)/44Ti values for the cco2 particle data
# Print out a few statistics for the data set, and then make a histogram too
# Repeat the same process with the data in log space, which is more useful
# Window the peaks... ADD TO THIS LATER
 
# Last modified 7/10/17 by Greg Vance

# I seldom actually use Numpy on Saguaro, but it will be great for this
import numpy as np
# Use Matplotlib for the histogram plotting
import matplotlib.pyplot as plt

# Giant CSV file containing all the per-particle data for the cco2 simulation
CCO2_PLOTTING_FILE = "/home/gsvance/results/plotting/cco2_plotting.out"
# Names of the histogram output images
HISTOGRAM_OUTPUT = "histogram.png"
LOG_HISTOGRAM_OUTPUT = "log_histogram.png"

# Limits for windowing the two peaks in log space
PEAK_1 = (2.0, 3.0)
PEAK_2 = (3.5, 4.5)

# Main program, called at the bottom of this file
def main():
	# Print a starting message for the user
	print "Aquiring (Fe+56Ni) / 44Ti ratio data from cco2 simulation..."
	# Read the first line of the data file to get the column headers
	with open(CCO2_PLOTTING_FILE, "r") as data_file:
		headers = data_file.readline().strip().split(", ")
	# Find which columns of the file have the data we need
	col_Fe = headers.index("A_{Fe}")
	col_56Ni = headers.index("A_{56Ni}")
	col_44Ti = headers.index("A_{44Ti}")
	# Use Numpy's handy loadtxt function to read that data from file into arrays
	data_Fe, data_56Ni, data_44Ti = np.loadtxt(CCO2_PLOTTING_FILE, delimiter=", ",
		skiprows=1, usecols=(col_Fe, col_56Ni, col_44Ti), unpack=True)
	# Calculate the actual list of ratios that I want to analyze
	Fe_Ti = (data_Fe + data_56Ni) / data_44Ti
	# Remove any useless values that are either zero or NaN
	Fe_Ti = Fe_Ti[np.nonzero(Fe_Ti)]
	Fe_Ti = Fe_Ti[np.isfinite(Fe_Ti)]
	# Print the size of the usable data set
	print "\nUsable nonzero values:", Fe_Ti.size
	# Print a few of the basic ordering statistics to get sense of the range
	print "\nOrdering statistics:"
	print "          minimum:", scientific(np.amin(Fe_Ti))
	print "   5th percentile:", scientific(np.percentile(Fe_Ti, 5.))
	print "     1st quartile:", scientific(np.percentile(Fe_Ti, 25.))
	print "           median:", scientific(np.median(Fe_Ti))
	print "     3rd quartile:", scientific(np.percentile(Fe_Ti, 75.))
	print "  95th percentile:", scientific(np.percentile(Fe_Ti, 95.))
	print "          maximum:", scientific(np.amax(Fe_Ti))
	# Print a few statistics for the average and spread of the data
	print "\nAverage and spread statistics:"
	print "      mean:", scientific(np.mean(Fe_Ti))
	print "   std dev:", scientific(np.std(Fe_Ti))
	print "  variance:", scientific(np.var(Fe_Ti))
	# Make a Matplotlib histogram of the data
	print "\nMaking histogram of data..."
	plt.figure("Histogram")
	n, bins, patches = plt.hist(Fe_Ti, 100, (1.0, 1e6), facecolor="red")
	# Add labels and save the histogram to file
	plt.xlabel("(Fe + 56Ni) / 44Ti")
	plt.ylabel("Bin count")
	plt.title("Iron/Titanium Ratios for cco2 Particles")
	plt.savefig(HISTOGRAM_OUTPUT, dpi=100)
	# Take the log of all data and repeat the analysis in log space
	print "\nRepeating statistical analysis in log space..."
	log_Fe_Ti = np.log10(Fe_Ti)
	# Print the same sets of statistics once again in log space
	print "\nOrdering statistics in log space:"
	print "          minimum:", rounded(np.amin(log_Fe_Ti))
	print "   5th percentile:", rounded(np.percentile(log_Fe_Ti, 5.))
	print "     1st quartile:", rounded(np.percentile(log_Fe_Ti, 25.))
	print "           median:", rounded(np.median(log_Fe_Ti))
	print "     3rd quartile:", rounded(np.percentile(log_Fe_Ti, 75.))
	print "  95th percentile:", rounded(np.percentile(log_Fe_Ti, 95.))
	print "          maximum:", rounded(np.amax(log_Fe_Ti))
	print "\nAverage and spread statistics in log space:"
	print "      mean:", rounded(np.mean(log_Fe_Ti))
	print "   std dev:", rounded(np.std(log_Fe_Ti))
	print "  variance:", rounded(np.var(log_Fe_Ti))
	# Make a Matplotlib histogram of the logged data
	print "\nMaking histogram of log space data..."
	plt.figure("Log Histogram")
	n, bins, patches = plt.hist(log_Fe_Ti, 90, (0.0, 6.0), facecolor="blue")
	# Add labels and save the histogram to file again
	plt.xlabel("log((Fe + 56Ni) / 44Ti)")
	plt.ylabel("Bin count")
	plt.title("Log of Iron/Titanium Ratios for cco2 Particles")
	plt.savefig(LOG_HISTOGRAM_OUTPUT, dpi=100)
	# Window out the data for each of the two peaks in log space
	print "\nWindowing two peaks in log space data..."
	peak1 = log_Fe_Ti[(log_Fe_Ti >= PEAK_1[0]) & (log_Fe_Ti <= PEAK_1[1])]
	peak2 = log_Fe_Ti[(log_Fe_Ti >= PEAK_2[0]) & (log_Fe_Ti <= PEAK_2[1])]
	# Print average and spread stats for each peak
	print "\nStatistics for peak 1 [%.1f, %.1f]:" % (PEAK_1)
	print "      mean:", rounded(np.mean(peak1))
	print "   std dev:", rounded(np.std(peak1))
	print "  variance:", rounded(np.var(peak1))
	print "\nStatistics for peak 2 [%.1f, %.1f]:" % (PEAK_2)
	print "      mean:", rounded(np.mean(peak2))
	print "   std dev:", rounded(np.std(peak2))
	print "  variance:", rounded(np.var(peak2))
	# Print a blank line to end
	print

# Shortcut function for printing a number in nice scientific notation
def scientific(flt):
	return "%.3e" % (flt)

# Shortcut function to print a nicely rounded floating point number
def rounded(flt):
	return "%.3f" % (flt)

main()

