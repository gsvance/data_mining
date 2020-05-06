# File wrapper class to streamline the act of reading lots CSV files in DM postprocessing
# Class opens the file and returns lines one by one as split lists of the line entries
# Checks that the line's particle ID matches the desired one and returns [] if not
# Previously a part of the file dm_postprocessing.py, but it is now encapsulated here

# Last modified 6 May 2020 by Greg Vance

class Particler:
	# Initialize the object and start reading the given file
	def __init__(self, filename):
		# Store the name of the file as an attribute
		self.filename = filename
		# Open the designated file for reading
		self.file = open(self.filename, 'r')
		# The SDF files from cco2 are... special. Do we have the honor?
		self.cco2 = ( filename.find("r3g_1M_cco2_sph.") != -1 )
		# Flag for when all particles in the file are exhaused
		self.empty = False
		# Set up the ID tracker attribute with a negative dummy value
		self.next_id = -999
		# Set up a dummy value for the file's header entries
		self.header = []
		# Read the first line from the file
		self._get_line()
	# Get the actual next line from the file and split it into a list
	def _get_line(self):
		# Read a string from the file for the next line
		line = self.file.readline()
		# If nothing came out, then signal that the file is empty
		if line == "":
			self.empty = True
			return
		# Remove the '\n' and split the line into its CSV entries
		split_line = line.strip().split(", ")
		# Convert the line's particle ID to an integer
		try:
			new_id = int(split_line[0])
		# This error will occur when reading alphabetic header lines
		except ValueError:
			# Might as well save the header line since we have it
			if self.header == []:
				self.header = split_line
			# Check for if the file has a repeat header line
			elif self.header == split_line:
				print "Warning: repeated header in file %s" % (self.filename)
			# If there are multiple headers and they don't match, that's a problem
			else:
				err = "unmatched header lines in file %s" % (self.filename)
				raise ValueError(err)
			# Keep looking for actual data; get the next line from the file
			self._get_line()
			return
		# Check whether burn_query went screwy and make a file with repeated IDs
		if new_id > self.next_id:
			# Update to the next ID number if it's a sensible one
			self.next_id = new_id
		# Otherwise, the next ID number is apparently either repeated or smaller
		else: # new_id <= self.next_id
			# Raise an error and print some info about it to the user
			err = "repeated or unsorted ID in file %s" % (self.filename)
			err += "\n new_id %d is <= next_id %d" % (new_id, self.next_id)
			raise ValueError(err)
		# Save the line for a future call of the get_next() method
		self.next_line = split_line
	# Return the next line of the file if the ID matches, and [] otherwise
	def get_next(self, id):
		# When next particle is later than ID or file is empty, return []
		if self.empty or id < self.next_id:
			return []
		# If the ID matches the next ID, then return the stored line
		elif id == self.next_id:
			# Hold onto the next line for a second
			got_line = self.next_line
			# The object needs to retrieve the NEXT line
			self._get_line()
			# Now return the one that matched
			return got_line
		# This should never happen if the file is sorted properly
		else: # id > self.next_id
			# But it *does* happen for cco2 since the particle number changes
			if self.cco2:
				# Forget about this particle ID and just move on
				self._get_line()
				return self.get_next(id)
			else:
				# Something, somewhere is very wrong
				err = "requested ID %d is higher than was expected" % (id)
				err += "\n current ID %d was not requested" % (self.next_id)
				err += "\n file name: %s" % (self.filename)
				raise ValueError(err)
	# Read the file's header line and return the column index of column_name
	def find_column(self, column_name):
		# Before searching, make sure there's a header to search through
		if self.header == []:
			raise ValueError("file %s has no header to search" % (self.filename))
		# Search the header line for the given column name string
		return self.header.index(column_name)
	# Method to return whether the file is out of particles
	def is_empty(self):
		return self.empty
	# Close the file in preparation for the object's destruction
	def close(self):
		self.file.close()

