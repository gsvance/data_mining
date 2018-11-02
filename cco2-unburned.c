// Modified version of entropy for extracting unburned yields from cco2
// Identities of the 20 network isotopes must be inferred from other sims
// Infering those led me astray... seems that n, p, and 4He are at the end

// Last edited 9/5/17 by Greg Vance

/* 	
	Entropy
	Cut-to-purpose version of SDF reader, the Kludgey and Highly
	Manual SDF reader. It gets the job done though. 
	
	Open the SDF file to be opened in your ascii compatible text 
	reader of choice and grab the struct declaration up top and 
	paste it over the struct below. Now open the SDF file to be
	opened in your favorite hex editor and find the byte-length of
	the header (top of file to line break following EOH) and 
	set the value of int offset accordingly, likewise with the value of 
	nobjects, if you're lucky the header will state explicitly how many
	values are in the vector (usually appended to the  end of the struct) 
	otherwise it's time to do some byte math. Now simply modify the 
	actions of the for loop as desired for  your purposes and your 
	ready to compile and have at. Easy, Right? As it's currently
	configured it will output the temp, U, U_dot, and rho
	along with the identity tag and position for every particle in the 
	SDF files loaded into a csv files with a header row suitable
	for mangling further with C, Excel, Paraview, etc.
	
	Someday I might kludge a way of finding the header length (etc etc) 
	into this program and make it a proper SDF reader, but today is 
	not that day. 
	
	~JMS - 2015
	
	
	Useage
	./entropy [SDF Files] 
*/

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>

// Particle structure taken from the cco2 SDF file headers
typedef struct {
    double x, y, z;             /* position of body */
    float mass;                 /* mass of body */
    float vx, vy, vz;           /* velocity of body */
    float u;                    /* internal energy */
    float h;                    /* smoothing length */
    float rho;                  /* density */
    float drho_dt;              /* time derivative of rho */
    float udot;                 /* time derivative of u */
    float ax, ay, az;           /* acceleration */
    float lax, lay, laz;        /* acceleration at tpos-dt */
    float phi;                  /* potential */
    float idt;                  /* timestep */
    float pr;           /* pressure */
    unsigned int nbrs;          /* number of neighbors */
    unsigned int ident;         /* unique identifier */
    unsigned int windid;        /* wind id */
    float temp;                 /* temperature */
    float Y_el;                  /* for alignment */
    float mfp;                  /* mean free path */
    float f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20;
} particle;

// The identities of the 20 network isotopes as best I can infer from the other sims
// These are from 50Am, using interactive Python to dissect the .unburned.out file header
// !! The isotopes from 50Am are wrong and have been commented out at this point !!
// Instead, we took the first three isotopes n, p, and 4He and put them at the end
//int iso_nz[20] = {0, 1, 2, 6, 8, 10, 12, 14, 15, 16, 18, 20, 20, 21, 22, 24, 26, 26, 27, 28};
int iso_nz[20] = {6, 8, 10, 12, 14, 15, 16, 18, 20, 20, 21, 22, 24, 26, 26, 27, 28, 0, 1, 2};
//int iso_nn[20] = {1, 0, 2, 6, 8, 10, 12, 14, 16, 16, 18, 20, 24, 23, 22, 24, 26, 30, 29, 28};
int iso_nn[20] = {6, 8, 10, 12, 14, 16, 16, 18, 20, 24, 23, 22, 24, 26, 30, 29, 28, 1, 0, 2};

/*
Here are some notes on extracting the isotope data from the particle struct.
The final line in the particle struct stores all the unburned yields data:
	- f1..f20 are the mass fractions X for each nucleus.
	- The isotopes these correspond to are NOT the same as for other sims.
	- The iso_nz and iso_nn arrays are here to label the 20 isotopes.
There are 20 isotopes in the SNSPH network that is being used here.
The cco2 SDF files don't have those two extra isotopes like other sims do.
Extraction should probably only be used for the final timestep SDF files.
Earlier files can have unburned yields that just haven't burned YET.
*/

// Declare the function for measuring the header length, which is defined later
int getoffset(FILE * fp);

int main(int argc, char *argv[])
{
	// Declarations
	int h, j, i, sz, nobj;
	char * filename;
	char out_file[500];
	int offset;
	particle part;
	FILE * fp, * ofp;

	// Print an error meassage if called with no command line arguments
	if (argc == 1) 
	{
		fprintf(stderr, "Usage: %s SDF File(s)\n", argv[0]);
		exit(1);
   	}

	// Loop over the arguments and read each file given
	for (h = 1; h < argc; h++)
	{
		// Store the input file anem and construct the output file name
		filename = argv[h];
		strcpy(out_file, argv[h]);
		strcat(out_file, ".unburned.out");

		// Open the input and output files
		fp = fopen(filename, "rb");
		ofp = fopen(out_file, "w");

		// Work out the byte length of the header
		offset = getoffset(fp);

		// Seek the end of the file, with zero offset from that position
		fseek(fp, 0L, SEEK_END);
		sz = ftell(fp);

		// Use the length of the file to figure out the number of particles
		nobj = (sz - offset) / sizeof(particle);

		// Seek the beginning of the particle data in the file
		fseek(fp, offset, SEEK_SET);

		// Print a CSV header for the output file, including Z and N labels for each isotope
		fprintf(ofp, "ID, Mass");
		for (j = 0; j < 20; j++)
			fprintf(ofp, ", nz=%d:nn=%d", iso_nz[j], iso_nn[j]);
		fprintf(ofp, "\n");

		// Loop over the particles in the file and write data to the output file
		for (i = 0; i < nobj; i++)
		{
			// Read in a particle from the file
			fread(&part, sizeof(particle), 1, fp);

			// Print the PID number,particle mass, and isotope abundances to the output file
			fprintf(ofp, "%u, %g, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e\n",
                part.ident, part.mass,
                part.f1, part.f2, part.f3, part.f4, part.f5, part.f6, part.f7, part.f8, part.f9, part.f10,
                part.f11, part.f12, part.f13, part.f14, part.f15, part.f16, part.f17, part.f18, part.f19, part.f20);
		}

		// Close the input and output files
		fclose(fp);
		fclose(ofp);
	}

	return 0;
}

// Function for figuring out the header length of an arbitrary SDF file
int getoffset(FILE * fp)
{
    // Delarations and the sequence that indicates the header's end
    int offset, matched, length;
    char eoh[] = "\n# SDF-EOH";
    length = strlen(eoh);

    // Read the header one char at a time, keeping track of how many match the header end
    for (offset = matched = 0; matched < length; offset++)
    {
        if (getc(fp) == eoh[matched])
            matched++;
        else
            matched = 0;
    }

    // Move past any extra newlines at the end of the header
    for (; getc(fp) != '\n'; offset++);

    // Rewind the file pointer to the start of the file again
    rewind(fp);

    // Set the offset one ahead into the start of the data, and return the value
    return offset + 1;
}

