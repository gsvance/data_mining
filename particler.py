# File wrapper class to streamline the act of reading lots CSV files in postprocessing
# Class opens the file and returns lines one by one as split lists of the line entries
# Checks that the line's particle ID matches the desired one and returns [] if not
# Previously a part of the file postprocessing.py, but it is now encapsulated here

# Last edited 4/3/17 by Greg Vance

class Particler:
	# Initialize the object and start reading the given file
	def __init__(self, filename):
		# Open the designated file for reading
		self.file = open(filename, 'r')
		# The SDF files from cco2 are... special. Do we have the honor?
		self.cco2 = ( filename.find("r3g_1M_cco2_sph.") != -1 )
		# Flag for when all particles in the file are exhaused
		self.empty = False
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
			self.next_id = int(split_line[0])
		# Error occurs for alphabetic headers, get the next line instead
		except ValueError:
			self._get_line()
			return
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
				raise ValueError("ID %s is higher than expected??" % (id))
	# Method to return whether the file is out of particles
	def is_empty(self):
		return self.empty
	# Close the file in preparation for the object's destruction
	def close(self):
		self.file.close()

