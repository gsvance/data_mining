#!/usr/bin/env python

# Extract the peak density and density at peak temp from each simulation
# Write them to files in this directory for analysis

# Greg Vance, 4/4/17

import os
import sys

# So sn_utils and particler can be imported
sys.path.append("/home/gsvance/data_mining/")

import sn_utils as sn
from particler import Particler

SN_DATA = "/home/gsvance/sn_data/"
SN_SIMS = ["50Am", "cco2", "g292-j4c", "jet3b"]

for sim in SN_SIMS:

	head = SN_DATA + sim
	paths = sn.get_paths(head)
	sdf_dir = paths["sdf"]

	sdf_files = sn.sdf_list(paths, mode="early", dotout=True)
	sdfs = [Particler(os.path.join(paths["sdf"], s)) for s in sdf_files]

	outfilename = sim + "_density.txt"
	outfile = open(outfilename, "w")

	outfile.write("id, peak_density, density_at_peak_temp\n")

	id = 0

	while not all([s.is_empty() for s in sdfs]):

		if id % 50000 == 0:
			print "particle " + str(id)

		lines = [s.get_next(id) for s in sdfs]
		if all([line == [] for line in lines]):
			id += 1
			continue

		rho_temp = []

		for line in lines:
			if line != []:
				rho = float(line[7])
				temp = float(line[4])
				rho_temp.append((rho, temp))

		peak_rho = max(rho_temp, key=lambda x : x[0])[0]
		rho_at_peak_temp = max(rho_temp, key=lambda x : x[1])[0]

		outfile.write(str(id) + ", " + str(peak_rho) + ", " + \
			str(rho_at_peak_temp) + "\n")

		id += 1

	outfile.close()

	for s in sdfs:
		s.close()

