// Modified version of JMS's SDF Reader just for the cco2 simulation SDF files
// Includes an offset utility function to find the byte length of the header
// Fear not Jack, you no longer need to use a hex editor to figure that out
// Also, I added a lot of comments to make it more clear what the code does

// Last edited 31 Dec 2020 by Greg Vance

/* 	
	SDF Reader
	A kludgey and highly manual way of reading SDF files 
	but hey, they're self-describing so why not get your hands 
	dirty with binary IO every once in awhile.
	
	Open the SDF file to be opened in your ascii compatible text 
	reader of choice and grab the struct declaration up top and 
	paste it over the struct below. Now open the SDF file to be
	opened in your favorite hex editor and find the byte-length of
	the header (top of file to line break following EOH) and 
	set the value of int offset accordingly, likewise with the value of 
	nobjects, if you're lucky the header will state explicitly how many
	values are in the vector (usually appended to the  end of the struct, 
	otherwise it's time to do some byte math. Now simply modify the 
	actions of the for loop as desired for  your purposes and your 
	ready to compile and have at. Easy, Right?
	
	Someday I might kludge a way of finding the header length (etc etc) 
	into this program and make it a proper SDF reader, but today is 
	not that day.
	
	~Jack M. Sexton - 2014
	
	Now figures out the # of objects reasonably well and works for all
	data-sets conforming to the structure declared currently 
	(jet3b, jet5c, etc). 
	~JMS 2015
	
	Useage
	./sdf_reader [SDF Files] 
*/

#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <string.h>

// Particle struct taken from the cco2 SDF file headers
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

// Declare the header length function that is defined after main
int getoffset(FILE * fp);

int main(int argc, char *argv[])
{
	// Declarations
	int h, i, sz, nobj;
	char * filename;
	char out_file[500];
	int offset;
	particle part;
	FILE * fp, * ofp;

	// Print error message if called with no command line arguments
	if (argc == 1) 
	{
		fprintf(stderr, "Usage: %s SDF File(s) \n", argv[0]);
		exit(1);
	}

	// Loop over the command line arguments and read each file in turn
	for (h = 1; h < argc; h++)
	{
		// Store the current file name and constuct the output file name
		filename = argv[h];
		strcpy(out_file, argv[h]);
		strcat(out_file, ".out");

		// Open the input file and output file
		fp = fopen(filename, "rb");
		ofp = fopen(out_file, "w");

		// Work out the SDF header length for the input file
		offset = getoffset(fp);

		// Find the position (offset by 0 from it) of the end of the file
		fseek(fp, 0L, SEEK_END);
		sz = ftell(fp);

		// Work out how many particles are stored in the file's binary data
		nobj = (sz - offset) / sizeof(particle);

		// Write the CSV header line to the output file
		fprintf(ofp, "ID, X_Pos, Y_Pos, Z_Pos, Temp, U, U_dot, rho, V_x, V_y, V_z, A_x, A_y, A_z, h, Mass, Y_e\n");

		// Set the file pointer to the position of the end of the SDF header (data starts here)
		fseek(fp, offset, SEEK_SET);

		// Read each particle from the file in succesion and print a corresponding line to the output file
		for (i = 0; i < nobj; i++)
		{
			fread(&part, sizeof(particle), 1, fp);
			fprintf(ofp, "%d, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g\n",
				part.ident, part.x, part.y, part.z, part.temp, part.u, part.udot, part.rho, part.vx, part.vy, part.vz, part.ax, part.ay, part.az, part.h, part.mass, part.Y_el);
		}

		// Close the input and output files
		fclose(fp);
		fclose(ofp);
	}

	return 0;
}

// Function for finding the header length of an SDF file
int getoffset(FILE * fp)
{
	// Delarations and the signal that indicates the header's end
	int offset, matched, length;
	char eoh[] = "\n# SDF-EOH";
	length = strlen(eoh);

	// Read the file one char at a time, keeping track of how many match the header end
	for (offset = matched = 0; matched < length; offset++)
	{
		if (getc(fp) == eoh[matched])
			matched++;
		else
			matched = 0;
	}

	// Move past any extra newlines
	for (; getc(fp) != '\n'; offset++);

	// Rewind the file pointer to the start of the file
	rewind(fp);

	// Set the offset one more ahead into the start of the data, and return its value
	return offset + 1;
}

