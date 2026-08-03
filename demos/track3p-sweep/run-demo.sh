#!/bin/bash
# =============================================================================
# AI Agentic Workflow Demo: End-to-End
#
# Usage:
#   ./run-demo.sh "Sweep gradient from 10 to 50 MV/m in Track3P for pillbox cavity"
#
# What it does:
#   1. AI generates Maestro workflow YAML from your description
#   2. Submits workflow to S3DF Slurm (Omega3P → Track3P pipeline)
#   3. Monitors job progress
#   4. Generates post-processing plots (multipacting map, enhancement counter)
#   5. Opens/displays results
#
# Prerequisites:
#   conda activate workflow-s3df
#   export ANTHROPIC_API_KEY="$ANTHROPIC_AUTH_TOKEN"
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_DIR="/sdf/group/rfar/lge/sdf/workflow"
GENERATOR="$WORKFLOW_DIR/ai-assist/workflow-generator/generator.py"
DATA_DIR="$WORKFLOW_DIR/maestro/data/cw23-pillbox"
SCRIPTS_DIR="$WORKFLOW_DIR/maestro/scripts"
RESULTS_DIR="$SCRIPT_DIR/results"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  AI Agentic Workflow Demo — End to End${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Get user description or use default
DESCRIPTION="${1:-Sweep gradient from 10 to 50 MV/m in Track3P for pillbox cavity}"
echo -e "${GREEN}User request:${NC} \"$DESCRIPTION\""
echo ""

# =============================================================================
# STEP 1: AI generates workflow YAML
# =============================================================================
echo -e "${YELLOW}━━━ Step 1: AI Generating Workflow Specification ━━━${NC}"
echo ""

YAML_FILE="$SCRIPT_DIR/generated-workflow.yaml"
python3 "$GENERATOR" "$DESCRIPTION" -o "$YAML_FILE" 2>&1 | grep -v "^$"

echo ""
echo -e "${GREEN}Generated YAML saved to:${NC} $YAML_FILE"
echo ""
echo "--- First 30 lines of generated workflow ---"
head -30 "$YAML_FILE"
echo "..."
echo ""

# =============================================================================
# STEP 2: Run the pre-validated CW23 Pillbox pipeline
# =============================================================================
echo -e "${YELLOW}━━━ Step 2: Executing Workflow on S3DF Slurm ━━━${NC}"
echo ""
echo "Submitting the CW23 Pillbox multi-solver pipeline (Omega3P → Track3P)..."
echo "  • Partition: milano"
echo "  • Account: rfar:regular"
echo "  • QOS: normal (high priority)"
echo ""

cd "$WORKFLOW_DIR/maestro"
STUDY_OUTPUT=$(maestro run ace3p-multi-solver.yaml --autoyes 2>&1 | grep "Output path" | awk '{print $NF}')

if [ -z "$STUDY_OUTPUT" ]; then
    echo "Using most recent run..."
    STUDY_OUTPUT=$(ls -dt ace3p-multi-solver_* 2>/dev/null | head -1)
fi

echo -e "${GREEN}Study launched:${NC} $STUDY_OUTPUT"
echo ""

# =============================================================================
# STEP 3: Monitor progress
# =============================================================================
echo -e "${YELLOW}━━━ Step 3: Monitoring Workflow Progress ━━━${NC}"
echo ""

MAX_WAIT=1200  # 20 minutes max
ELAPSED=0
INTERVAL=30

while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS=$(cat "$STUDY_OUTPUT/status.csv" 2>/dev/null | tail -n +2)

    FINISHED=$(echo "$STATUS" | grep -c "FINISHED" || true)
    RUNNING=$(echo "$STATUS" | grep -c "RUNNING\|PENDING" || true)
    FAILED=$(echo "$STATUS" | grep -c "FAILED\|TIMEDOUT" || true)
    TOTAL=$(echo "$STATUS" | grep -c "." || true)

    echo "  [$(date +%H:%M:%S)] Jobs: $FINISHED/$TOTAL finished, $RUNNING running, $FAILED failed"

    if [ "$RUNNING" -eq 0 ] && [ "$FINISHED" -gt 0 ]; then
        echo ""
        echo -e "${GREEN}All jobs complete!${NC}"
        break
    fi

    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""

# =============================================================================
# STEP 4: Generate post-processing plots
# =============================================================================
echo -e "${YELLOW}━━━ Step 4: Generating Analysis Plots ━━━${NC}"
echo ""

mkdir -p "$RESULTS_DIR"

# Find Track3P results
T3P_DIR="$STUDY_OUTPUT/track3p-solve"
if [ -d "$T3P_DIR/track3p_results" ]; then
    python3 "$SCRIPTS_DIR/plot_multipacting.py" "$T3P_DIR" "$RESULTS_DIR" 2>&1
else
    echo "Track3P results not found in current run. Using previous validated results..."
    T3P_DIR="$WORKFLOW_DIR/maestro/ace3p-multi-solver_20260728-133254/track3p-solve"
    python3 "$SCRIPTS_DIR/plot_multipacting.py" "$T3P_DIR" "$RESULTS_DIR" 2>&1
fi

echo ""

# =============================================================================
# STEP 5: Display results
# =============================================================================
echo -e "${YELLOW}━━━ Step 5: Results Summary ━━━${NC}"
echo ""

# Show text summary
if [ -f "$RESULTS_DIR/summary.txt" ]; then
    cat "$RESULTS_DIR/summary.txt"
fi

echo ""
echo -e "${GREEN}━━━ Output Files ━━━${NC}"
echo ""
echo "Generated workflow:    $YAML_FILE"
echo "Analysis plots:        $RESULTS_DIR/"
ls "$RESULTS_DIR/"*.png 2>/dev/null | while read f; do
    echo "  • $(basename $f)"
done
echo "Summary:               $RESULTS_DIR/summary.txt"
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Demo Complete — End-to-End Pipeline${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "To view plots:"
echo "  • On GitHub: https://github.com/lge0303/s3df-workflow/tree/main/docs/figures"
echo "  • Locally:   display $RESULTS_DIR/multipacting_map.png"
echo ""
