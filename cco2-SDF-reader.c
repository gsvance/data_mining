// Modified version of JMS's SDF Reader just for the cco2 simulation SDF files

// Last edited 6/20/16 by Greg Vance

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

int getoffset(FILE * fp);

int main(int argc, char *argv[])
{

	int h,i,sz,nobj;
	char *filename;
	char out_file[100];
	int offset;
	particle part;

	if (argc == 1) 
	{
		fprintf(stderr, "Usage: %s SDF File(s) \n", argv[0]);
		exit(1);
	}

	for (h=1; h < argc; ++h)
	{
		filename=argv[h];
		strcpy(out_file, argv[h]);
		strcat(out_file, ".out");
		
		FILE *fp = fopen(filename, "rb");
		FILE *ofp = fopen(out_file,"w");

		offset = getoffset(fp);

		fseek(fp, 0L, SEEK_END);
		sz = ftell(fp);
		nobj = (sz-offset)/sizeof(particle);

		/*
		Comment from 6/2/17, Greg Vance:
		I don't actually know what this next block of code is doing for me or why it's even here.
		Looks like it goes to the offset position of the first particle and reads that into memory.
		Then we print the header line to the output file, though I'm not sure why that happens here.
		Then we rewind to the beginning of the file, and go back to the first particle before the loop starts.
		The particle read into memory doesn't get used, and gets read in again when the loop starts.
		Jack Sexton wrote this originally in his SDF-reader.c. It doesn't seem to have a real point.
		I am tempted to simply remove the extraneous lines, but they might be important somehow...
		If I figure it out at some point, I will have to be sure to add an explanatory comment here.
		*/
		fseek(fp,offset,SEEK_SET);
		fread(&part,sizeof(particle),1,fp);
		fprintf(ofp, "ID, X_Pos, Y_Pos, Z_Pos, Temp, U, U_dot, rho, V_x, V_y, V_z, h, Mass, Y_e\n");
		rewind(fp);
		fseek(fp,offset,SEEK_SET);
		for (i = 0; i < nobj; ++i)
		{
			fread(&part,sizeof(particle),1,fp);
			fprintf(ofp, "%d, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g\n",
				part.ident, part.x, part.y, part.z, part.temp, part.u, part.udot, part.rho, part.vx, part.vy, part.vz, part.h, part.mass, part.Y_el);
		}
		
		fclose(fp);
		fclose(ofp);
	}

	return 0;
}

int getoffset(FILE * fp)
{
	int offset, matched;
	char eoh[] = "\n# SDF-EOH";

	for (offset = matched = 0; matched < strlen(eoh); offset++)
	{
		if (getc(fp) == eoh[matched]) matched++;
		else matched = 0;
	}
	for (; getc(fp) != '\n'; offset++);

	rewind(fp);
	return offset+1;
}

