#!/usr/bin/env python

# Check how much the peak densities differ from the densities at peak temp
# Output some statistics for each simualtion on how much they differ

# Greg Vance, 4/4/17

import numpy as np

SN_SIMS = ["50Am", "cco2", "g292-j4c", "jet3b"]

print "rel_diff = (peak_rho - rho_at_peak_temp) / rho_at_peak_temp"

for sim in SN_SIMS:

	filename = sim + "_density.txt"

	id, peak_rho, rho_at_peak_temp = \
		np.loadtxt(filename, delimiter=", ", skiprows=1, unpack=True)

	rel_diff = (peak_rho - rho_at_peak_temp) / rho_at_peak_temp

	nonzero = rel_diff[rel_diff != 0.0]

	print sim
	print "  # nonzero rel diff:", len(nonzero), "/", len(rel_diff), "=", \
		len(nonzero) / float(len(rel_diff))
	print "  mean nonzero rel diff:", np.mean(nonzero)
	print "  median nonzero rel diff:", np.median(nonzero)
	print "  maximum rel diff:", np.max(nonzero)

