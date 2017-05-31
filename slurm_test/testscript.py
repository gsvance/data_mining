#!/usr/bin/env python
 
#SBATCH -p cluster                  # Send this job to the default partition
#SBATCH -n 1                        # number of cores
#SBATCH -t 0-00:10                  # wall time (D-HH:MM)
##SBATCH -A drzuckerman             # Account to pull cpu hours from (commented out)
#SBATCH -o slurm.%j.out             # STDOUT (%j = JobId)
#SBATCH -e slurm.%j.err             # STDERR (%j = JobId)
#SBATCH --mail-type=END,FAIL        # notifications for job done & fail
#SBATCH --mail-user=gsvance@asu.edu # send-to address

for i in range(100):
    print i

x = 1/0

