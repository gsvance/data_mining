// This program extracts a list of all particle ID numbers from HDF5 files
// Its input should be a set of HDF5 files that the program is to read
// Its output is a plain text list of every particle ID in those HDF5 files
// Program is called with a list of input file names on the command line
// The name of the output file must also be passed in, preceeded by -o
// For example: ./hdf5_pid_list abc.h5 def.h5 ghi.h5 jkl.h5 -o output.txt

// Last edited 7/24/17 by Greg Vance

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <SE.h>

// Global variable to store the called name of the program
char * argv0;

// Prototypes for helper functions that are defined later
int ends_with(char * str, char * end);
int * read_hdf5_ids(char * hdf5name, int * n_particles);
int cmpint(const void * i1, const void * i2);
void write_text_ids(char * outfilename, int * all_ids, int tot_ids);

int main(int argc, char * argv[])
{
	// Declarations
	int c, n_hdf5, i, tot_ids, j, k;
	char * outfilename;
	int * n_ids, * all_ids;
	int ** ids;

	// Save the value of argv[0] globally
	argv0 = argv[0];

	// Check that command is called with enough arguments
	if (argc < 4)
	{
		fprintf(stderr, "%s: not enough arguments\n", argv0);
		exit(1);
	}

	// Parse the set of input arguments
	outfilename = NULL;
	for (c = 1; c < argc; c++)
	{
		// If the output file name comes next, then parse that
		if (strcmp(argv[c], "-o") == 0)
		{
			if (c < argc - 1)
				c++;
			else
				break;

			if (!ends_with(argv[c], ".h5"))
			{
				if (outfilename == NULL)
					outfilename = argv[c];
				else
				{
					fprintf(stderr, "%s: multiple output files?\n", argv0);
					exit(2);
				}
			}
			else
			{
				fprintf(stderr, "%s: output file %s is an HDF5\n", argv0, argv[c]);
				exit(2);
			}
		}
		// Otherwise, just make sure the argument is an HDF5 file
		else if (!ends_with(argv[c], ".h5"))
		{
			fprintf(stderr, "%s: argument %s not an HDF5 file\n", argv0, argv[c]);
			exit(2);
		}
	}
	if (outfilename == NULL)
	{
		fprintf(stderr, "%s: no output file name\n", argv0);
		exit(2);
	}

	// Work out how many HDF5 files we are dealing with
	n_hdf5 = argc - 3;

	// Allocate space to hold the lengths of each array of ID numbers
	n_ids = malloc(n_hdf5 * sizeof(int));
	if (n_ids == NULL)
	{
		fprintf(stderr, "%s: failure allocating n_ids\n", argv0);
		exit(3);
	}

	// Allocate space to hold pointers to the arrays of particle IDs
	ids = malloc(n_hdf5 * sizeof(int *));
	if (ids == NULL)
	{
		fprintf(stderr, "%s: failure allocating ids\n", argv0);
		exit(3);
	}

	// Read the arrays of ID numbers from each of the HDF5 files
	for (i = 0, c = 1; i < n_hdf5 && c < argc; c++)
	{
		// Skip over the output file name
		if (strcmp(argv[c], "-o") == 0)
			c++;
		// Otherwise, read the HDF5 file
		else
		{
			printf("Now reading file %d of %d\n", i + 1, n_hdf5);
			ids[i] = read_hdf5_ids(argv[c], &n_ids[i]);
			++i;
		}
	}

	// Figure out the total number of IDs and allocate enough space for them all
	tot_ids = 0;
	for (i = 0; i < n_hdf5; i++)
		tot_ids += n_ids[i];
	all_ids = malloc(tot_ids * sizeof(int));
	if (all_ids == NULL)
	{
		fprintf(stderr, "%s: failure allocating all_ids\n", argv0);
		exit(3);
	}

	// Compile the arrays of ID numbers into a single big array
	k = 0;
	for (i = 0; i < n_hdf5; i++)
		for (j = 0; j < n_ids[i]; j++)
			all_ids[k++] = ids[i][j];

	// Sort the big ID number array with qsort
	qsort(all_ids, tot_ids, sizeof(int), cmpint);

	// Write the array of ID numbers to the output plaintext file
	write_text_ids(outfilename, all_ids, tot_ids);

	// Free all allocated memory
	for (i = 0; i < n_hdf5; i++)
		free(ids[i]);
	free(n_ids);
	free(ids);
	free(all_ids);

	// Print a message for the user indicating completion
	printf("List of IDs compiled and saved to %s\n", outfilename);

	return 0;
}

// Return whether the end chars of the string str match the string end
int ends_with(char * str, char * end)
{
	// Declarations
	int len_str, len_end;
	char * str_end;

	// Find the lengths of each string
	len_str = strlen(str);
	len_end = strlen(end);

	// The str string must be at least as long as the end string
	if (len_str < len_end)
		return 0;

	// Find where the end string would have to begin in the str string
	str_end = &(str[len_str - len_end]);

	// Now return whether the two strings match
	return (strcmp(str_end, end) == 0);
}

// Read out the list of particle IDS from the given HDF5 file name
// Return a pointer to allocated array of IDs and the length of that array
int * read_hdf5_ids(char * hdf5name, int * n_particles)
{
	// Declarations
	int file_id, parts;
	int * id_list;

	// Print a progress message for the user
	printf("Opening file %s\n", hdf5name);

	// Use the SE library to open the HDF5 file
	file_id = SEopen(hdf5name);

	// Use SEncycles to acertain the number of particles in the file
	parts = SEncycles(file_id);

	// Allocate enough space to store all the particle IDs that are coming
	id_list = malloc(parts * sizeof(int));
	if (id_list == NULL)
	{
		fprintf(stderr, "%s: failure allocating id_list in read_hdf5_ids\n", argv0);
		exit(4);
	}

	// Use SEcycles to read the array of particle IDs from file
	SEcycles(file_id, id_list, parts);

	// Close the HDF5 file that the SE library still has open
	SEclose(file_id);

	// Return the number of particle IDs read from the file and the data pointer
	*n_particles = parts;
	return id_list;
}

// Compare two ints for the qsort function
int cmpint(const void * i1, const void * i2)
{
	// Cast void *s to int *s and dereference to take their difference
	return ( (*(int *)i1) - (*(int *)i2) );
}

// Write the full list of ID numbers out to the plain text file
void write_text_ids(char * outfilename, int * all_ids, int tot_ids)
{
	// Declarations
	FILE * fp;
	int i;

	// Open the file in write mode
	fp = fopen(outfilename, "w");

	// To help out later, put the number of IDs on the first line of the file
	fprintf(fp, "n_ids=%d\n", tot_ids);

	// Write each ID number to the file on a new line
	for (i = 0; i < tot_ids; i++)
		fprintf(fp, "%d\n", all_ids[i]);

	// Close the file
	fclose(fp);
}

