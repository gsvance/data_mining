// Program for updating the total yields from a sim using unburned yields data
// Pass the total yields and unburned yields files in as command line arguments
// The identities of those two files are determined by their file name endings
// Calling this without an _yields.out and a .unburned.out file is an error!

// Last modified 7/9/17 by Greg Vance

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// The two file name endings this program looks for on the command line
#define TOTAL_YIELDS_END "_yields.out"
#define UNBURNED_YIELDS_END ".unburned.out"

// New file name ending for the updated total yields output file
#define UPDATED_YIELDS_END "_updated_yields.out"

// Constants to keep track of the sizes of the two nuclear networks
#define SNSPH_NETWORK 20
#define BURN_NETWORK 524

// Constant factors for converting masses between unit systems
#define SOLAR_MASS 1.98855e33  // The mass of the sun in grams
#define SNSPH_MASS (1e-6 * SOLAR_MASS)  // SNSPH mass in grams (10^-6 Msun)

// Struct to store data from one line of the total yields file
typedef struct {
	int nn, nz;
	double mass;
	float percent;
} isotope;

// Struct to store data from one line of the unburned yields file
typedef struct {
	unsigned int pid;
	float mass;
	float mass_frac[SNSPH_NETWORK];
} particle;

// Global arrays to store proton and neutron numbers for the unburned yields
int unburned_nz[SNSPH_NETWORK];
int unburned_nn[SNSPH_NETWORK];

// Declarations of helper functions that are defined later
int ends_with(char * str, char * end);
void read_total(isotope data[], char * file_name);
particle * read_unburned(char * file_name, int * particles);
void sum_unburned(double totals[], particle * data, int particles);
void update_totals(isotope totals[], double unburned[]);
double pairs_sum(double * array, int n);
void write_updated(isotope data[], char * file_name);

int main(int argc, char * argv[])
{
	// Declarations
	char * total_yields;
	char * unburned_yields;
	char output_file[500];
	isotope total_data[BURN_NETWORK];
	particle * unburned_data;
	int particles;
	double unburned_totals[SNSPH_NETWORK];

	// Check for the correct number of command line arguments, as stated above
	if (argc != 3)
	{
		fprintf(stderr, "%s: please provide TWO file arguments\n", argv[0]);
		exit(1);
	}

	// Identify the two file arguments and raise errors if identification fails
	if (ends_with(argv[1], TOTAL_YIELDS_END))
		total_yields = argv[1];
	else if (ends_with(argv[2], TOTAL_YIELDS_END))
		total_yields = argv[2];
	else
	{
		fprintf(stderr, "%s: no total yields file ending in \"%s\"\n",
			argv[0], TOTAL_YIELDS_END);
		exit(2);
	}
	if (ends_with(argv[2], UNBURNED_YIELDS_END))
		unburned_yields = argv[2];
	else if (ends_with(argv[1], UNBURNED_YIELDS_END))
		unburned_yields = argv[1];
	else
	{
		fprintf(stderr, "%s: no unburned yields file ending in \"%s\"\n",
			argv[0], UNBURNED_YIELDS_END);
		exit(2);
	}

	// Construct the output file name from the total yields file name
	strcpy(output_file, total_yields);
	output_file[strlen(output_file) - strlen(TOTAL_YIELDS_END)] = '\0';
	strcat(output_file, UPDATED_YIELDS_END);

	// Read in the data from both of the input files
	read_total(total_data, total_yields);
	unburned_data = read_unburned(unburned_yields, &particles);

	// Sum the unburned yields data over all the particles
	sum_unburned(unburned_totals, unburned_data, particles);

	// Update the appropriate total yields isotopes with the unburned yields sums
	update_totals(total_data, unburned_totals);

	// Write the newly updated yields data to the output file
	write_updated(total_data, output_file);

	// Free the allocated memory from reading the unburned yields file
	free(unburned_data);

	// Print a general success message for the program user
	printf("Updated yields were produced and saved to %s\n", output_file);

	return 0;
}

// Return whether the ending of the string str is matches the string end
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

// Read the total yields data from file into a prepared array
void read_total(isotope data[], char * file_name)
{
	// Declarations
	FILE * fp;
	int l;

	// Open the file that has the data
	fp = fopen(file_name, "r");

	// Read one line at a time into the array of structs using fscanf
	for (l = 0; l < BURN_NETWORK; l++)
		fscanf(fp, "nn = %d nz = %d mass = %lf (%f%%)\n",
			&(data[l].nn), &(data[l].nz), &(data[l].mass), &(data[l].percent));

	// Close the file
	fclose(fp);
}

// Allocate memory for the unburned yields data and read it all in
// This includes the Z and N values that go into our global arrays
// Return the number of particles read from the file via an int pointer
particle * read_unburned(char * file_name, int * particles)
{
	// Declarations
	FILE * fp;
	int start_len, i;
	char file_start[] = "ID, Mass";
	char buffer[100];
	int lines, c;
	particle * data;
	int l;

	// Open up the unburned yields CSV file
	fp = fopen(file_name, "r");

	// Read the start of the header line to make sure it matches what we expect
	start_len = strlen(file_start);
	for (i = 0; i < start_len; i++)
		buffer[i] = fgetc(fp);
	buffer[i] = '\0';
	if (strcmp(buffer, file_start) != 0)
	{
		fprintf(stderr, "unburned yields file does not match expectations\n");
		exit(3);
	}

	// Use the header line to fill in the Z and N values in our global arrays
	for (i = 0; i < SNSPH_NETWORK; i++)
		fscanf(fp, ", nz=%d:nn=%d", &(unburned_nz[i]), &(unburned_nn[i]));

	// Rewind to the beginning of the file and make sure to skip the header line
	rewind(fp);
	while (fgetc(fp) != '\n');

	// Count the number of data lines in the file
	i = lines = 0;
	do
	{
		c = fgetc(fp);

		// Count any line that has more characters on it than just a newline
		if (c == '\n' || c == EOF)
		{
			if (i > 0)
			{
				i = 0;
				lines++;
			}
		}

		// Count the number of characters on each line
		else
			i++;
	}
	while (c != EOF);

	// Allocate the memory we will need for the number of particles in the file
	data = malloc(lines * sizeof(particle));
	if (data == NULL)
	{
		fprintf(stderr, "could not allocate memory for unburned yields data\n");
		exit(3);
	}

	// Rewind to the start of the file and skip the header line (again)
	rewind(fp);
	while (fgetc(fp) != '\n');

	// Read all of the data lines from the file into the particle array
	for (l = 0; l < lines; l++)
	{
		fscanf(fp, "%u, %g", &(data[l].pid), &(data[l].mass));
		for (i = 0; i < SNSPH_NETWORK; i++)
			fscanf(fp, ", %e", &(data[l].mass_frac[i]));
	}

	// Close the file
	fclose(fp);

	// Return the number of particles (lines in the file) via pointer
	*particles = lines;

	// Return the address of the allocated memory block directly
	return data;
}

// Sum the unburned yields masses into a pre-existing totals array
void sum_unburned(double totals[], particle * data, int particles)
{
	// Declarations
	double * workspace;
	int i, j;

	// Allocate a workspace of double-precision floats for this operation
	workspace = malloc(particles * sizeof(double));
	if (workspace == NULL)
	{
		fprintf(stderr, "could not allocate summation workspace\n");
		exit(4);
	}

	// Loop over every isotope in the SNSPH network and do the summations
	for (i = 0; i < SNSPH_NETWORK; i++)
	{
		// Multiply each particle's mass fraction by its mass to get isotope masses
		for (j = 0; j < particles; j++)
			workspace[j] = data[j].mass * data[j].mass_frac[i];

		// Calculate the sum of the list of doubles and convert the mass to grams
		totals[i] = pairs_sum(workspace, particles);
		totals[i] *= SNSPH_MASS;
	}

	// Free the alloacted workspace memory
	free(workspace);
}

// Update the appropriate isotopes from the total yields with unburned data
void update_totals(isotope totals[], double unburned[])
{
	// Declarations
	int i, j;
	double masses[BURN_NETWORK];
	double total_mass;

	// Loop over every isotope of the the total yields data
	for (i = 0; i < BURN_NETWORK; i++)
	{
		// Check every pairing of isotopes between the two sets for matches
		for (j = 0; j < SNSPH_NETWORK; j++)
			if (totals[i].nz == unburned_nz[j] && totals[i].nn == unburned_nn[j])

				// When a match is found, add on all the unburned yields
				totals[i].mass += unburned[j];

		// Keep track of the final mass of every isotope
		masses[i] = totals[i].mass;
	}

	// Sum up the total mass of all isotopes for the simulation
	total_mass = pairs_sum(masses, BURN_NETWORK);

	// Use the total mass to adjust the isotope mass percentages
	for (i = 0; i < BURN_NETWORK; i++)
		totals[i].percent = 100.0 * totals[i].mass / total_mass;
}

// Sum an array of n doubles in a numerically-stable pairwise fashion
// The array is used as workspace and is RUINED by this operation
double pairs_sum(double * array, int n)
{
    // Declarations
    int spacing, i;

    // Sum the numbers in the array pairwise to hopefully reduce errors
    for (spacing = 1; spacing < n; spacing *= 2)
        for (i = 0; i + spacing < n; i += 2 * spacing)
            array[i] += array[i + spacing];

    // Return the first element, which now contains the sum
    return array[0];
}

// Write the updated total yields data out to a new file
void write_updated(isotope data[], char * file_name)
{
	// Declarations
	FILE * fp;
	int i;

	// Open the new file to be written to
	fp = fopen(file_name, "w");

	// Loop over the data in the array and write all of it to file
	for (i = 0; i < BURN_NETWORK; i++)
		fprintf(fp, "nn = %d nz = %d mass = %e (%.2f%%)\n",
			data[i].nn, data[i].nz, data[i].mass, data[i].percent);

	// Close the file
	fclose(fp);
}
