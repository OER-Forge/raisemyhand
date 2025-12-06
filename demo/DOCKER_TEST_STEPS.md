# Docker Demo Mode Test Steps

## Current Status
- ✅ Container `raisemyhand-app-1` is running on port 8000
- ✅ Need to stop it before testing demo mode

---

## Test Steps

### Step 1: Stop Current Container
```bash
docker-compose down
```

**Expected:** Container stops, port 8000 freed

---

### Step 2: Generate Demo Data (One-time, before Docker)
```bash
# Generate Physics 101 context JSON files
python demo/generate_context.py --context physics_101
```

**Expected Output:**
```
======================================================================
🎯 Generating Demo Context: physics_101
📖 Course: Physics 101: Classical Mechanics
📍 Output: demo/data/physics_101
======================================================================
✓ Generated instructors.json with 2 instructors
✓ Generated classes.json with 1 classes
✓ Generated meetings.json with 5 meetings
✓ Generated questions.json with 60 questions
✓ Generated config.json
✓ Total Votes: 320
```

**Verify files created:**
```bash
ls -la demo/data/physics_101/
# Should show: instructors.json, classes.json, meetings.json, questions.json, config.json
```

---

### Step 3: Start Docker in Demo Mode
```bash
DEMO_CONTEXT=physics_101 docker-compose -f docker-compose.yml -f docker-compose.demo.yml up
```

**Expected Output:**
```
🎯 Starting RaiseMyHand in DEMO mode
📦 Loading demo context: physics_101
======================================================================
🎯 Loading Demo Context: physics_101
======================================================================

📚 Loading 2 instructors...
  ✓ Created instructor: Dr. Sarah Einstein (@sarah_einstein)
  ✓ Created instructor: Prof. James Maxwell (@james_maxwell)

🔑 Loading API keys...
  ✓ Created API key for Dr. Sarah Einstein: rmh_...
  ✓ Created API key for Prof. James Maxwell: rmh_...

📖 Loading 1 classes...
  ✓ Created class: Physics 101: Classical Mechanics

🎓 Loading 5 class meetings...
  ✓ Created meeting: Day 1: Introduction to Kinematics (code: ...)
  ✓ Created meeting: Day 3: Newton's Laws of Motion (code: ...)
  ✓ Created meeting: Day 5: Work, Energy, and Power (code: ...)
  ✓ Created meeting: Day 8: Linear Momentum and Collisions (code: ...)
  ✓ Created meeting: Day 10: Rotational Motion (code: ...)

❓ Loading 60 questions...
  ✓ Loaded 5 questions...
  ✓ Loaded 10 questions...
  ...
  ✓ Loaded all 60 questions

======================================================================
✅ Demo context loaded successfully!
======================================================================

📊 Summary:
  Instructors: 2
  API Keys: 2
  Classes: 1
  Meetings: 5

🔑 API Keys:
  Dr. Sarah Einstein: rmh_abc123...
  Prof. James Maxwell: rmh_xyz789...

🎓 Meeting Access:
  Day 1: Introduction to Kinematics
    Student URL: http://localhost:8000/student?code=abc123...
    Instructor URL: http://localhost:8000/instructor?code=xyz789...
  [... more meetings ...]

🚀 Starting application server...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Step 4: Verify Demo Data in Browser

1. **Copy a Student URL** from the output above
2. **Open in browser**: `http://localhost:8000/student?code=...`
3. **Verify:**
   - ✓ Meeting title shows (e.g., "Day 1: Introduction to Kinematics")
   - ✓ Questions are visible
   - ✓ Vote counts are displayed (not all zeros)
   - ✓ Can upvote questions

4. **Copy an Instructor URL** from the output
5. **Open in browser**: `http://localhost:8000/instructor?code=...`
6. **Verify:**
   - ✓ All questions visible
   - ✓ Vote counts accurate
   - ✓ Can mark as answered

---

### Step 5: Verify Database (Optional)

In another terminal while container is running:
```bash
# Access the demo database
docker exec -it raisemyhand-app-1 sqlite3 /app/data/demo_raisemyhand.db

# Check vote counts
SELECT 
    q.id, 
    q.text, 
    q.upvotes as claimed, 
    COUNT(qv.id) as actual,
    CASE WHEN q.upvotes = COUNT(qv.id) THEN '✓' ELSE '✗' END as match
FROM questions q 
LEFT JOIN question_votes qv ON q.id = qv.question_id
GROUP BY q.id
LIMIT 10;

# Exit sqlite
.exit
```

**Expected:** All rows should show '✓' in match column

---

### Step 6: Stop Demo Mode
```bash
# Press Ctrl+C to stop, then:
docker-compose down
```

---

## Alternative: Test Locally (Without Docker)

If Docker has issues, test locally:

```bash
# Step 1: Generate data (same as above)
python demo/generate_context.py --context physics_101

# Step 2: Load into local database
python demo/load_demo_context.py physics_101

# Step 3: Start app locally
uvicorn main:app --reload

# Step 4: Access URLs from loader output
```

---

## Troubleshooting

### Issue: "Context directory not found"
**Fix:** You forgot Step 2. Run `python demo/generate_context.py --context physics_101`

### Issue: Port 8000 already in use
**Fix:** Make sure you ran `docker-compose down` first

### Issue: No questions showing in browser
**Check:**
1. Look for errors in Docker logs
2. Verify database has data:
   ```bash
   docker exec -it raisemyhand-app-1 sqlite3 /app/data/demo_raisemyhand.db "SELECT COUNT(*) FROM questions;"
   ```

### Issue: Votes all showing as 0
**Check:**
1. Verify question_votes table:
   ```bash
   docker exec -it raisemyhand-app-1 sqlite3 /app/data/demo_raisemyhand.db "SELECT COUNT(*) FROM question_votes;"
   ```
2. If count is 0, there was a vote loading issue

---

## Clean Up After Testing

### Keep Demo Database
```bash
# Demo database is at: data/demo_raisemyhand.db
# Your original database is safe at: data/raisemyhand.db
```

### Remove Demo Database
```bash
rm data/demo_raisemyhand.db
```

### Restart Normal Mode
```bash
docker-compose up
```

---

## Next Steps After Successful Test

- [ ] Generate all 5 contexts
- [ ] Test loading multiple contexts
- [ ] Update main README with demo instructions
- [ ] Consider committing generated JSON to repo
