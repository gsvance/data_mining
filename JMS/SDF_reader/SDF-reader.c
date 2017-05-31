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

int main(int argc, char *argv[])
{

	int h,i,sz,nobj;
	char *filename;
	char out_file[50];
	int offset=1600;
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

		fseek(fp, 0L, SEEK_END);
		sz = ftell(fp);
		nobj = (sz-offset)/sizeof(particle);
		
		fseek(fp,offset,SEEK_SET);
		fread(&part,sizeof(particle),1,fp);
		fprintf(ofp, "ident, x, y, z, density, temp, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d, %d:%d \n ",
							part.p1, part.m1, part.p2, part.m2, part.p3, part.m3, part.p4, part.m4, part.p5, part.m5, part.p6, part.m6, part.p7, part.m7, part.p8, part.m8, part.p9, part.m9, part.p10, part.m10, part.p11, part.m11, part.p12, 
							part.m12, part.p13, part.m13, part.p14, part.m14, part.p15,	part.m15, part.p16, part.m16, part.p17, part.m17, part.p18, part.m18, part.p19, part.m19, part.p20, part.m20 );
		rewind(fp);
		fseek(fp,offset,SEEK_SET);
		for (i = 0; i < nobj; ++i)
		{
			fread(&part,sizeof(particle),1,fp);
			fprintf(ofp, "%d, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g, %g \n ",
					part.ident, part.x, part.y, part.z, part.rho, part.temp, part.f1, part.f2, part.f3, part.f4, part.f5, part.f6, part.f7, part.f8, part.f9, part.f10, 
					part.f11, part.f12, part.f13, part.f14, part.f15, part.f16, part.f17, part.f18, part.f19, part.f20 );
		}
		
		fclose(fp);
		fclose(ofp);
	}
	return 0;
	
}

