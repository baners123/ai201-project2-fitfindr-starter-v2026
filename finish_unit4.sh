#!/bin/bash
set -e

echo "1. Checking current project..."
python -c "import scenarios; print('scenario validation:', scenarios.validate())"
python test.py

echo
echo "2. Running BEFORE evaluation..."
python run_eval.py --label before

BEFORE=$(ls -t results/run_*_before.md | head -1)
echo "Before report: $BEFORE"

echo
echo "3. Scoring BEFORE report..."
python score_unit4.py "$BEFORE" | tee results/before_score.txt

echo
echo "4. Committing BEFORE evidence..."
git add results "$BEFORE" score_unit4.py
git commit -m "Record Unit 4 before evaluation" || true
git push

echo
echo "5. Applying the single Unit 4 improvement..."
cp tools_after.py tools.py

echo
echo "6. Checking improved search..."
python -c "from tools import search_listings; print([(x['title'], x['price']) for x in search_listings('vintage graphic tee', max_price=30)[:5]])"
python test.py

echo
echo "7. Committing the improvement..."
git add tools.py
git commit -m "Improve listing relevance ranking"
git push

echo
echo "8. Running AFTER evaluation..."
python run_eval.py --label after

AFTER=$(ls -t results/run_*_after.md | head -1)
echo "After report: $AFTER"

echo
echo "9. Scoring AFTER report..."
python score_unit4.py "$AFTER" | tee results/after_score.txt

echo
echo "10. Committing AFTER evidence..."
git add results
git commit -m "Record Unit 4 after evaluation"
git push

echo
echo "11. Final checks..."
python test.py
git status
git log --oneline -12

echo
echo "Finished."
echo "Before: $BEFORE"
echo "After:  $AFTER"
echo
echo "Send README.md plus results/before_score.txt and results/after_score.txt to ChatGPT"
echo "if you want the final README verdict text checked before submission."
