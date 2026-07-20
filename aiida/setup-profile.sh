#!/bin/bash
# AiiDA profile setup for S3DF
# Run this once to configure AiiDA for local development.

set -e

echo "=== AiiDA Profile Setup for S3DF ==="

# Initialize AiiDA with SQLite (quick setup, no PostgreSQL needed)
echo "1. Setting up AiiDA profile with SQLite..."
verdi presto

# Register S3DF as a computer
echo "2. Registering S3DF Slurm computer..."
verdi computer setup \
  --label s3df \
  --hostname localhost \
  --transport core.local \
  --scheduler core.slurm \
  --work-dir /sdf/scratch/rfar/{username}/aiida_work \
  --mpirun-command "srun -n {tot_num_mpiprocs}" \
  --mpiprocs-per-machine 128 \
  --non-interactive

verdi computer configure core.local s3df --non-interactive

# Register ACE3P codes
echo "3. Registering ACE3P codes..."

ACE3P_BIN=/sdf/group/rfar/lge/sdf/ace3p/bin

verdi code create core.code.installed \
  --label omega3p \
  --computer s3df \
  --filepath-executable ${ACE3P_BIN}/omega3p \
  --default-calc-job-plugin ace3p.omega3p \
  --non-interactive

verdi code create core.code.installed \
  --label track3p \
  --computer s3df \
  --filepath-executable ${ACE3P_BIN}/track3p \
  --default-calc-job-plugin ace3p.track3p \
  --non-interactive

verdi code create core.code.installed \
  --label acdtool \
  --computer s3df \
  --filepath-executable ${ACE3P_BIN}/acdtool \
  --default-calc-job-plugin ace3p.acdtool \
  --non-interactive

echo ""
echo "=== Setup Complete ==="
echo "Verify with: verdi status"
echo "List codes:  verdi code list"
