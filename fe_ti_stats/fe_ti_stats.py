#!/usr/bin/env python

# Quick script for running statistics to look at the Fe/Ti ratios from cco2
# We are interested in comparing them to the Cas A observations by Grefenstette
# Work out the full list of (Fe+56Ni)/44Ti values for the cco2 particle data
# Print out a few statistics for the data set, and then make a histogram too
# Repeat the same process with the data in log space, which is more useful
# Window the two prominent peaks in log space and print a few stats for them
# Try to quantify the physical conditions corresponding to each of the peaks
 
# Last modified 7/17/17 by Greg Vance

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
PEAK_2 = (3.0, 5.0)

# Main program, called at the bottom of this file
def main():
	# Print a starting message for the user
	print "Aquiring (Fe+56Ni)/44Ti ratio data from cco2 simulation..."
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
	data_Fe_Ti = (data_Fe + data_56Ni) / data_44Ti
	# Remove any useless values that are either zero or NaN
	usable_data = (data_Fe_Ti != 0.0) & np.isfinite(data_Fe_Ti)
	Fe_Ti = data_Fe_Ti[usable_data]
	# Print the size of the usable data set
	print "\nUsable nonzero values:", np.sum(usable_data)
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
	print "     mean:", scientific(np.mean(Fe_Ti))
	print "  std dev:", scientific(np.std(Fe_Ti))
	# Make a Matplotlib histogram of the data
	print "\nMaking histogram of data..."
	plt.figure("Histogram")
	n, bins, patches = plt.hist(Fe_Ti, 100, (0.0, 5e3), facecolor="red")
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
	print "     mean:", rounded(np.mean(log_Fe_Ti))
	print "  std dev:", rounded(np.std(log_Fe_Ti))
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
	window1 = (log_Fe_Ti >= PEAK_1[0]) & (log_Fe_Ti <= PEAK_1[1])
	window2 = (log_Fe_Ti >= PEAK_2[0]) & (log_Fe_Ti <= PEAK_2[1])
	peak1_Fe_Ti = log_Fe_Ti[window1]
	peak2_Fe_Ti = log_Fe_Ti[window2]
	# Print average and spread stats for each peak
	print "\nStatistics for peak 1, interval [%.1f, %.1f]:" % (PEAK_1)
	print "     mean:", rounded(np.mean(peak1_Fe_Ti))
	print "  std dev:", rounded(np.std(peak1_Fe_Ti))
	print "\nStatistics for peak 2, interval [%.1f, %.1f]:" % (PEAK_2)
	print "     mean:", rounded(np.mean(peak2_Fe_Ti))
	print "  std dev:", rounded(np.std(peak2_Fe_Ti))
	# To explore the physical conditions in these two peaks, we need more data
	print "\nAquiring peak temperature and density data from cco2 simulation..."
	# Go back to the data file and find the peak temps and densitites for this
	col_peak_temp = headers.index("peak temp")
	col_peak_rho = headers.index("peak density")
	data_peak_temp, data_peak_rho = np.loadtxt(CCO2_PLOTTING_FILE, delimiter=", ",
		skiprows=1, usecols=(col_peak_temp, col_peak_rho), unpack=True)
	# Sift out the peak temp and density data corresponding to usable Fe/Ti values
	peak_temp = data_peak_temp[usable_data]
	peak_rho = data_peak_rho[usable_data]
	# From there, window the peak temp and density data for each of the two peaks
	peak1_peak_temp = peak_temp[window1]
	peak1_peak_rho = peak_rho[window1]
	peak2_peak_temp = peak_temp[window2]
	peak2_peak_rho = peak_rho[window2]
	# Print a few stats for the typical physical conditions at each peak
	print "\nConditions for peak 1 (mean Fe/Ti %.1f):" % (np.mean(peak1_Fe_Ti))
	print "     mean peak temp:", scientific(np.mean(peak1_peak_temp)), "K"
	print "  std dev peak temp:", scientific(np.std(peak1_peak_temp)), "K"
	print "      mean peak rho:", scientific(np.mean(peak1_peak_rho)), "g/cm^3"
	print "   std dev peak rho:", scientific(np.std(peak1_peak_rho)), "g/cm^3"
	print "\nConditions for peak 2 (mean Fe/Ti %.1f):" % (np.mean(peak2_Fe_Ti))
	print "     mean peak temp:", scientific(np.mean(peak2_peak_temp)), "K"
	print "  std dev peak temp:", scientific(np.std(peak2_peak_temp)), "K"
	print "      mean peak rho:", scientific(np.mean(peak2_peak_rho)), "g/cm^3"
	print "   std dev peak rho:", scientific(np.std(peak2_peak_rho)), "g/cm^3"
	# Print a blank line to end
	print

# Shortcut function for printing a number in nice scientific notation
def scientific(flt):
	return "%.3e" % (flt)

# Shortcut function to print a nicely rounded floating point number
def rounded(flt):
	return "%.3f" % (flt)

main()

