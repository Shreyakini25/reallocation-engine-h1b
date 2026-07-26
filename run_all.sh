#!/usr/bin/env bash
# Runs the full H-1B Reallocation Engine pipeline in the correct order.
# The GIGO gate is enforced by engine.py itself (it will halt if the gate
# fails), so this script doesn't need to check that separately -- but we
# run gigo_gate.py first anyway to show its standalone report too.
set -e  # stop immediately if any step fails -- don't paper over a real error

echo "=== 1. GIGO Gate (standalone report) ==="
python3 src/gigo_gate.py

echo ""
echo "=== 2. Engine (gate is enforced internally, then scores + reallocates) ==="
python3 src/engine.py

echo ""
echo "=== 3. Bias Audit ==="
python3 src/bias_audit.py

echo ""
echo "=== 4. Explainability Critique ==="
python3 src/explainability.py

echo ""
echo "=== 5. Causal & Counterfactual Analysis ==="
python3 src/causal_analysis.py

echo ""
echo "=== 6. Adversarial Robustness Test ==="
python3 src/adversarial.py

echo ""
echo "=== 7. Delegation Map + Hard-Stop Gate ==="
python3 src/delegation_hardstop.py

echo ""
echo "=== 8. Regenerate Uncertainty Figure ==="
python3 src/make_uncertainty_figure.py

echo ""
echo "=== ALL STEPS COMPLETE ==="
