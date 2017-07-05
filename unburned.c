// Modified version of JMS's 'entropy' for extracting the unburned yields

// Last edited 6/2/17 by Greg Vance

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
The final three lines in the particle struct store the unburned yields data:
	- f1..f22 are the mass fractions X for each nucleus.
	- p1..p22 are the proton numbers Z for each nucleus.
	- m1..m22 are the mass numbers A for each nucleus.
There are 22 isotopes in the SNSPH network that is being used here.
This should probably only be used for the final timestep SDF files.
Earlier files might have unburned yields that just haven't burned YET.
*/

int main(int argc, char *argv[])
{
	int h, i, sz, nobj;
	char * filename;
	char out_file[100];
	int offset = 1600;
	particle part;

	if (argc == 1) 
	{
		fprintf(stderr, "Usage: %s SDF File(s)\n", argv[0]);
		exit(1);
   	}

	for (h = 1; h < argc; h++)
	{
		filename = argv[h];
		strcpy(out_file, argv[h]);
		strcat(out_file, ".unburned.out");
		
		FILE *fp = fopen(filename, "rb");
		FILE *ofp = fopen(out_file, "w");

		fseek(fp, 0L, SEEK_END);
		sz = ftell(fp);
		nobj = (sz-offset) / sizeof(particle);
		fseek(fp, offset, SEEK_SET);

		fprintf(ofp, "ID\n");
		fprintf(ofp, "Z1, Z2, Z3, Z4, Z5, Z6, Z7, Z8, Z9, Z10, Z11, Z12, Z13, Z14, Z15, Z16, Z17, Z18, Z19, Z20, Z21, Z22\n");
		fprintf(ofp, "A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15, A16, A17, A18, A19, A20, A21, A22\n");
		fprintf(ofp, "X1, X2, X3, X4, X5, X6, X7, X8, X9, X10, X11, X12, X13, X14, X15, X16, X17, X18, X19, X20, X21, X22\n");

		for (i = 0; i < nobj; i++)
		{
			fread(&part, sizeof(particle), 1, fp);
			fprintf(ofp, "%u\n", part.ident);
			fprintf(ofp, "%d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d\n",
				part.p1, part.p2, part.p3, part.p4, part.p5, part.p6, part.p7, part.p8, part.p9, part.p10, part.p11,
				part.p12, part.p13, part.p14, part.p15, part.p16, part.p17, part.p18, part.p19, part.p20, part.p21, part.p22);
			fprintf(ofp, "%d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d, %d\n",
				part.m1, part.m2, part.m3, part.m4, part.m5, part.m6, part.m7, part.m8, part.m9, part.m10, part.m11,
				part.m12, part.m13, part.m14, part.m15, part.m16, part.m17, part.m18, part.m19, part.m20, part.m21, part.m22);
			fprintf(ofp, "%e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e, %e\n",
				part.f1, part.f2, part.f3, part.f4, part.f5, part.f6, part.f7, part.f8, part.f9, part.f10, part.f11,
				part.f12, part.f13, part.f14, part.f15, part.f16, part.f17, part.f18, part.f19, part.f20, part.f21, part.f22);
		}
		
		fclose(fp);
		fclose(ofp);
	}

	return 0;
}

