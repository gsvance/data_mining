#!/bin/bash
 
#SBATCH -p serial                   # Send this job to the serial partition
#SBATCH -n 1                        # number of cores
#SBATCH -t 0-12:00                  # wall time (D-HH:MM)
##SBATCH -A drzuckerman             # Account to pull cpu hours from (commented out)
#SBATCH -o slurm.%j.out             # STDOUT (%j = JobId)
#SBATCH -e slurm.%j.err             # STDERR (%j = JobId)
#SBATCH --mail-type=END,FAIL        # notifications for job done & fail
#SBATCH --mail-user=myemail@asu.edu # send-to address

module load gcc/4.9.2

for i in {1..100000}; do
  echo $RANDOM >> SomeRandomNumbers.txt
done

sort SomeRandomNumbers.txt

