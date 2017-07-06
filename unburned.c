// Modified version of JMS's entropy for extracting the unburned yields
// Uses Jack's first particle trick for making the CSV header
// Note that the last two isotopes in the network are intentionally unused

// Last edited 7/5/17 by Greg Vance

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

// Particle struct taken from SDF file headers
typedef struct
{
    double x, y, z;		/* position of body */
    float mass;			/* mass of body */
    float vx, vy, vz;		/* velocity of body */
    float u;			/* internal energy */
    float h;			/* smoothing length */
    float rho;			/* density */
    float drho_dt;              /* time derivative of rho */
    float udot;			/* time derivative of u */
    float ax, ay, az;		/* acceleration */
    float lax, lay, laz;	/* acceleration at tpos-dt */
    float phi;			/* potential */
    float idt;			/* timestep */
    unsigned int nbrs;          /* number of neighbors */
    unsigned int ident;		/* unique identifier */
    unsigned int windid;        /* wind id */
    float temp;                 /* temperature */
    float Y_el;                  /* for alignment */
    float f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f19,f20,f21,f22; 
    int p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16,p17,p18,p19,p20,p21,p22; 
    int m1,m2,m3,m4,m5,m6,m7,m8,m9,m10,m11,m12,m13,m14,m15,m16,m17,m18,m19,m20,m21,m22; 
} particle; 

/*
Here are some notes on extracting the isotope data from the particle struct.
The final three lines in the particle struct store the unburned yields data:
	- f1..f20 are the mass fractions X for each nucleus.
	- p1..p20 are the proton numbers Z for each nucleus.
	- m1..m20 are the neutron numbers N for each nucleus.
There are 20 isotopes in the SNSPH network that is being used here.
The last two isotopes (21 and 22) are unused and should be left ignored.
Extraction should probably only be used for the final timestep SDF files.
Earlier files can have unburned yields that just haven't burned YET.
*/

// Declaration of the isotope matching function defined after main
void match_pm(particle * p1, particle * p2);

int main(int argc, char *argv[])
{
	// Declarations, including the known header offset of 1600 bytes
	int h, i, sz, nobj;
	char * filename;
	char out_file[100];
	int offset = 1600;
	particle part, first;
	FILE * fp, * ofp;

	// Print an error if called with no command line arguments
	if (argc == 1) 
	{
		fprintf(stderr, "Usage: %s SDF File(s)\n", argv[0]);
		exit(1);
   	}

	// Read each file from the command line in turn
	for (h = 1; h < argc; h++)
	{
		// Store the input file name and construct the output file name
		filename = argv[h];
		strcpy(out_file, argv[h]);
		strcat(out_file, ".unburned.out");

		// Open the input and output files
		fp = fopen(filename, "rb");
		ofp = fopen(out_file, "w");

		// Seek the end of the file with zero offset from that position
		fseek(fp, 0L, SEEK_END);
		sz = ftell(fp);

		// Calculate the number of particles stored in the file
		nobj = (sz - offset) / sizeof(particle);

		// Seek the start of the particle data in the file and read the first particle
        fseek(fp, offset, SEEK_SET);
        fread(&first, sizeof(particle), 1, fp);

		// Use the isotope Z and N values from the first particle to print a CSV header for the output file
		fprintf(ofp, "ID, Mass, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, "
			"nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, "
			"nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d, nz=%d:nn=%d\n",
			first.p1, first.m1, first.p2, first.m2, first.p3, first.m3, first.p4, first.m4, first.p5, first.m5,
			first.p6, first.m6, first.p7, first.m7, first.p8, first.m8, first.p9, first.m9, first.p10, first.m10,
			first.p11, first.m11, first.p12, first.m12, first.p13, first.m13, first.p14, first.m14, first.p15, first.m15,
			first.p16, first.m16, first.p17, first.m17, first.p18, first.m18, first.p19, first.m19, first.p20, first.m20);

		// Rewind the file and set the pointer to the start of the data again
		rewind(fp);
        fseek(fp, offset, SEEK_SET);

		// Loop over the particles in the file and extract their unburned yields abundances
		for (i = 0; i < nobj; i++)
		{
			// Read in the next particle from the file and check its proton and neutron numbers
			fread(&part, sizeof(particle), 1, fp);
			match_pm(&part, &first);

			// Print the PID number, particle mass, and isotope abundances to the output file
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

// Check that two particles have EXACTLY the same proton and neutron numbers
// Ignore isotopes 21 and 22, which are to be ignored since the network has 20 isotopes
// I'm not taking any chances that something doesn't match for some silly reason
// Print an error and invoke the stdlib exit function if something doesn't jive
void match_pm(particle * part1, particle * part2)
{
	// Keep track of whether any check has failed
	int fail = 0;

	// Check every pair of proton and neutron numbers
	if (part1->p1 != part2->p1 || part1->m1 != part2->m1)
		fail = 1;
	if (part1->p2 != part2->p2 || part1->m2 != part2->m2)
		fail = 1;
	if (part1->p3 != part2->p3 || part1->m3 != part2->m3)
		fail = 1;
	if (part1->p4 != part2->p4 || part1->m4 != part2->m4)
		fail = 1;
	if (part1->p5 != part2->p5 || part1->m5 != part2->m5)
		fail = 1;
	if (part1->p6 != part2->p6 || part1->m6 != part2->m6)
		fail = 1;
	if (part1->p7 != part2->p7 || part1->m7 != part2->m7)
		fail = 1;
	if (part1->p8 != part2->p8 || part1->m8 != part2->m8)
		fail = 1;
	if (part1->p9 != part2->p9 || part1->m9 != part2->m9)
		fail = 1;
	if (part1->p10 != part2->p10 || part1->m10 != part2->m10)
		fail = 1;
	if (part1->p11 != part2->p11 || part1->m11 != part2->m11)
		fail = 1;
	if (part1->p12 != part2->p12 || part1->m12 != part2->m12)
		fail = 1;
	if (part1->p13 != part2->p13 || part1->m13 != part2->m13)
		fail = 1;
	if (part1->p14 != part2->p14 || part1->m14 != part2->m14)
		fail = 1;
	if (part1->p15 != part2->p15 || part1->m15 != part2->m15)
		fail = 1;
	if (part1->p16 != part2->p16 || part1->m16 != part2->m16)
		fail = 1;
	if (part1->p17 != part2->p17 || part1->m17 != part2->m17)
		fail = 1;
	if (part1->p18 != part2->p18 || part1->m18 != part2->m18)
		fail = 1;
	if (part1->p19 != part2->p19 || part1->m19 != part2->m19)
		fail = 1;
	if (part1->p20 != part2->p20 || part1->m20 != part2->m20)
		fail = 1;

	// If anything fails, kill the program and tell me
	if (fail)
	{
		fprintf(stderr, "There was a particle isotope mismatch!\n");
		exit(2);
	}
}

