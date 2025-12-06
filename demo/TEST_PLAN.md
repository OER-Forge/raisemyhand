# Demo Mode Test Plan

**Date**: December 6, 2024  
**Status**: Ready for Testing

---

## Pre-Flight Checklist

### ✅ Code Verification
- [x] Scripts compile without syntax errors
- [x] Vote generation logic verified
- [x] Database schema matches models (question_votes table exists)
- [x] Relationship resolution logic implemented
- [x] Duplicate detection in place

### ✅ Files Created
- [x] `demo/generate_context.py` - JSON generator
- [x] `demo/load_demo_context.py` - Database loader
- [x] `demo/README.md` - Usage documentation
- [x] `docker-compose.demo.yml` - Docker override
- [x] `DEMO_DATA_GENERATION_REPORT.md` - Full methodology

### 📋 Ready to Test
- [ ] Generate first context (physics_101)
- [ ] Load into database
- [ ] Verify data integrity
- [ ] Test with application

---

## Test Sequence

### Test 1: Generate Physics 101 Context
```bash
python demo/generate_context.py --context physics_101
```

**Expected Output:**
- Creates `demo/data/physics_101/` directory
- Generates 5 JSON files:
  - `instructors.json` (2 instructors)
  - `classes.json` (1 class)
  - `meetings.json` (5 meetings)
  - `questions.json` (~60 questions with votes)
  - `config.json` (system settings)

**Success Criteria:**
- ✓ All files created
- ✓ Valid JSON syntax
- ✓ ~300-350 total votes across questions
- ✓ No error messages

---

### Test 2: Load Physics 101 into Database
```bash
python demo/load_demo_context.py physics_101
```

**Expected Output:**
- Loads instructors, API keys, classes, meetings, questions, votes
- Prints summary with API keys and meeting URLs
- No error messages

**Success Criteria:**
- ✓ 2 instructors created
- ✓ 2 API keys generated
- ✓ 1 class created
- ✓ 5 meetings created (2 active, 3 ended)
- ✓ ~60 questions created
- ✓ Vote counts match (question.upvotes == COUNT(question_votes))

**Verification Queries:**
```sql
-- Check instructor count
SELECT COUNT(*) FROM instructors WHERE username LIKE '%einstein%' OR username LIKE '%maxwell%';

-- Check questions and votes
SELECT 
    q.id, 
    q.text, 
    q.upvotes as claimed, 
    COUNT(qv.id) as actual,
    CASE WHEN q.upvotes = COUNT(qv.id) THEN '✓' ELSE '✗' END as match
FROM questions q 
LEFT JOIN question_votes qv ON q.id = qv.question_id
WHERE q.meeting_id IN (SELECT id FROM class_meetings WHERE title LIKE '%Day%')
GROUP BY q.id
LIMIT 10;

-- Check meeting codes
SELECT id, title, meeting_code, instructor_code, is_active 
FROM class_meetings 
WHERE title LIKE 'Day%'
ORDER BY id;
```

---

### Test 3: Start Application with Demo Data
```bash
# Option A: Direct
uvicorn main:app --reload

# Option B: Docker (if testing docker compose)
DEMO_CONTEXT=physics_101 docker-compose -f docker-compose.yml -f docker-compose.demo.yml up
```

**Manual Testing:**
1. Access student URL from loader output
2. Verify questions are visible
3. Check vote counts display correctly
4. Access instructor URL
5. Verify instructor can see questions
6. Check API key works

---

### Test 4: Generate All Contexts (Optional)
```bash
for context in biology_200 calculus_150 chemistry_110 computer_science_101; do
    python demo/generate_context.py --context $context
    python demo/load_demo_context.py $context
done
```

**Expected Output:**
- 5 total contexts loaded
- 6 total instructors (physics has 2)
- 5 classes
- 25 meetings
- ~300 questions
- ~1500+ votes

---

## Potential Issues & Solutions

### Issue: "Context directory not found"
**Cause**: Trying to load before generating  
**Solution**: Run `generate_context.py` first

### Issue: "Instructor already exists"
**Cause**: Re-running loader on same data  
**Solution**: Normal behavior - loader skips duplicates. To start fresh:
```bash
mv data/raisemyhand.db data/raisemyhand_backup.db
python init_db_v2.py
```

### Issue: "UNIQUE constraint failed: question_votes.question_id, question_votes.student_id"
**Cause**: Duplicate student vote (unlikely but possible)  
**Status**: Non-fatal - loader continues, just skips duplicate

### Issue: Vote counts don't match
**Cause**: Logic error in vote generation  
**Debug**:
```sql
SELECT q.id, q.upvotes, COUNT(qv.id) as actual 
FROM questions q 
LEFT JOIN question_votes qv ON q.id = qv.question_id 
GROUP BY q.id 
HAVING q.upvotes != COUNT(qv.id);
```

---

## Rollback Plan

If testing fails:
```bash
# 1. Backup current database
cp data/raisemyhand.db data/raisemyhand_test_backup.db

# 2. Restore original
cp data/raisemyhand_backup.db data/raisemyhand.db

# 3. Or start fresh
rm data/raisemyhand.db
python init_db_v2.py
```

---

## Success Metrics

### Minimum Viable Test (Physics 101 only):
- [x] Generate completes without errors
- [ ] Load completes without errors
- [ ] All vote counts match: `question.upvotes == COUNT(question_votes)`
- [ ] Meeting URLs accessible
- [ ] Questions visible to students
- [ ] Instructor dashboard shows questions

### Full Test (All 5 contexts):
- [ ] All contexts generate successfully
- [ ] All contexts load without conflicts
- [ ] Total: 6 instructors, 5 classes, 25 meetings, ~300 questions
- [ ] Average 5.2 votes per question
- [ ] No duplicate key violations
- [ ] Application runs with all demo data

---

## Post-Test Actions

### If Successful:
1. ✓ Mark as production-ready in README
2. ✓ Generate all 5 contexts for repository
3. ✓ Update main README with demo mode instructions
4. ✓ Consider adding to CI/CD for testing

### If Issues Found:
1. Document issue in this file
2. Fix code
3. Re-test
4. Update DEMO_DATA_GENERATION_REPORT.md with corrections

---

## Test Log

### Run 1: [Date/Time]
**Context:** physics_101  
**Result:**  
**Notes:**  

### Run 2: [Date/Time]
**Context:** all contexts  
**Result:**  
**Notes:**  

---

**Tester:** ___________________  
**Sign-off:** ___________________
