# RaiseMyHand Issue Prioritization

**Last Updated:** 2025-12-04
**Current Status:** Phase 5 Complete (Navigation & UX)

---

## 🎯 Priority Tiers

### **TIER 1: CRITICAL - Address Immediately**

#### Issue #13: [START HERE] Request an API Key
- **Priority:** HIGHEST
- **Status:** Open
- **Type:** Operational/Help Desk
- **Description:** This is a help desk issue for users requesting API keys to test the demo at https://raisemyhand.hellmo.space
- **Action Required:** This should remain open as a permanent help desk ticket
- **Recommendation:** Pin this issue and add a template/automated response for handling API key requests

---

### **TIER 2: HIGH PRIORITY - Core Feature Completion**

These issues complete critical user-facing features and should be tackled next.

#### Issue #23: [PHASE 5] Add Markdown Editor and Renderer
- **Priority:** HIGH
- **Effort:** 6 hours
- **Status:** Open
- **Phase:** 5 (Enhanced Answers)
- **Why High Priority:**
  - Completes Phase 5 (only remaining Phase 5 task)
  - High user value - instructors need rich text formatting for answers
  - Relatively isolated change (no dependencies)
  - Backend API already exists
- **Dependencies:** None
- **Impact:** Improves instructor answer quality and student comprehension
- **Recommendation:** **START HERE** after reviewing this document

**Files to Modify:**
- `templates/instructor.html` - Add EasyMDE editor
- `templates/student.html` - Add marked.js and DOMPurify
- `static/js/instructor.js` - Initialize editor, handle save
- `static/js/student.js` - Render markdown safely
- `static/css/styles.css` - Style markdown content

**Libraries (CDN, no install):**
```html
<script src="https://unpkg.com/easymde/dist/easymde.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify/dist/purify.min.js"></script>
```

---

### **TIER 3: MEDIUM PRIORITY - Content Moderation (Phase 4)**

Complete Phase 4 features for content safety. These should be done in sequence.

#### Issue #19: [PHASE 4] Implement Profanity Filter
- **Priority:** MEDIUM
- **Effort:** 4 hours
- **Status:** Open
- **Phase:** 4 (Content Moderation)
- **Why Medium Priority:**
  - Important for classroom safety
  - Required before Issue #20
  - Database schema already supports it
- **Dependencies:** None
- **Impact:** Prevents inappropriate content in classroom settings
- **Recommendation:** Do AFTER Issue #23

**Implementation:**
- Client-side: `bad-words` library (npm or CDN)
- Server-side: `profanity-check` Python library
- Defense-in-depth approach (both client and server validation)
- Questions flagged, not rejected (instructor can review)

**Files to Modify:**
- `routes_questions.py` - Add profanity check logic
- `static/js/student.js` - Add client-side filter
- `requirements.txt` - Add `profanity-check==1.0.0`

---

#### Issue #20: [PHASE 4] Create Instructor Review Panel for Flagged Questions
- **Priority:** MEDIUM
- **Effort:** 6 hours
- **Status:** Open
- **Phase:** 4 (Content Moderation)
- **Why Medium Priority:**
  - Completes the profanity filter workflow
  - Gives instructors control over flagged content
- **Dependencies:** Issue #19 (profanity filter must exist first)
- **Impact:** Empowers instructors to moderate their classrooms
- **Recommendation:** Do AFTER Issue #19

**Implementation:**
- New API endpoints: GET flagged questions, POST approve/reject
- UI tab/section in instructor dashboard
- WebSocket real-time updates
- Rejected questions hidden from student view

**Files to Modify:**
- `routes_questions.py` - Add review endpoints
- `templates/instructor.html` - Add flagged questions UI
- `static/js/instructor.js` - Add review panel logic
- `static/css/styles.css` - Style flagged questions section

---

### **TIER 4: LOW PRIORITY - Nice-to-Have Features**

These can be deferred until core features are complete.

#### Issue #27: [PHASE 8] Write Instructor Documentation
- **Priority:** LOW (but valuable)
- **Effort:** 4 hours
- **Status:** Open
- **Phase:** 8 (Documentation)
- **Why Low Priority:**
  - No code changes required
  - Can be done anytime
  - More valuable after all features are complete
- **Dependencies:** None (but better to write after all features exist)
- **Impact:** Improves onboarding and reduces support burden
- **Recommendation:** Do when all user-facing features are complete

**Deliverables:**
- `docs/INSTRUCTOR_QUICKSTART.md`
- `docs/INSTRUCTOR_FAQ.md`
- `docs/INSTRUCTOR_TUTORIAL.md`
- `docs/TROUBLESHOOTING.md`

---

#### Issue #26: [PHASE 7] Add Admin Dashboard
- **Priority:** LOW
- **Effort:** 8 hours
- **Status:** Open
- **Phase:** 7 (Admin Dashboard)
- **Why Low Priority:**
  - Admin features are secondary to instructor/student experience
  - Current admin functionality is sufficient for MVP
  - Time-consuming implementation
- **Dependencies:** None
- **Impact:** Improves admin experience but not critical for core functionality
- **Recommendation:** Do LAST (or defer to post-launch)

**Features:**
- Instructor management (create, deactivate)
- System-wide statistics
- Class and meeting monitoring
- System health dashboard

**Files to Create:**
- `routes_admin.py` - New admin endpoints
- `templates/admin.html` - Admin dashboard UI
- `static/js/admin.js` - Admin dashboard logic

---

### **TIER 5: FUTURE/DEFERRED - Phase 9 Features**

These are advanced features for future development. Defer until after launch.

#### Issue #29: [PHASE 9] Add Admin Configuration Management
- **Priority:** FUTURE
- **Status:** Open
- **Phase:** 9
- **Recommendation:** Defer to post-launch

#### Issue #30: [PHASE 9] Enhance Admin Dashboard
- **Priority:** FUTURE
- **Status:** Open
- **Phase:** 9
- **Recommendation:** Defer to post-launch

#### Issue #31: [PHASE 9] Implement Admin Security Features
- **Priority:** FUTURE
- **Status:** Open
- **Phase:** 9
- **Recommendation:** Defer to post-launch

#### Issue #32: [PHASE 9] Add Bulk Instructor Management
- **Priority:** FUTURE
- **Status:** Open
- **Phase:** 9
- **Recommendation:** Defer to post-launch

---

## 📋 Recommended Execution Order

### **Sprint 1: Complete Phase 5** (6 hours)
1. ✅ Issue #23 - Markdown Editor and Renderer

### **Sprint 2: Complete Phase 4** (10 hours)
2. ✅ Issue #19 - Profanity Filter
3. ✅ Issue #20 - Instructor Review Panel

### **Sprint 3: Polish & Documentation** (4-12 hours)
4. ⚠️ Issue #27 - Instructor Documentation (4 hours)
5. ⚠️ Issue #26 - Admin Dashboard (8 hours) - OPTIONAL

### **Future Sprints: Phase 9**
6. 🔮 Issues #29-32 - Advanced admin features (defer)

---

## 🎯 Quick Decision Matrix

| Issue | Priority | Effort | User Value | Technical Risk | Recommendation |
|-------|----------|--------|------------|----------------|----------------|
| #23 (Markdown) | HIGH | 6h | High | Low | **DO NEXT** |
| #19 (Profanity) | MEDIUM | 4h | Medium | Low | **DO AFTER #23** |
| #20 (Review Panel) | MEDIUM | 6h | Medium | Low | **DO AFTER #19** |
| #27 (Docs) | LOW | 4h | Medium | None | **DO WHEN READY** |
| #26 (Admin UI) | LOW | 8h | Low | Medium | **DEFER** |
| #29-32 (Phase 9) | FUTURE | TBD | Low | TBD | **DEFER TO POST-LAUNCH** |
| #13 (Help Desk) | OPERATIONAL | N/A | N/A | N/A | **KEEP OPEN** |

---

## 🚀 Next Steps

### Immediate Action:
1. **Start with Issue #23 (Markdown Editor)** - 6 hours
   - Highest user value
   - Completes Phase 5
   - No dependencies
   - Low technical risk

### This Week:
2. **Complete Issue #19 (Profanity Filter)** - 4 hours
3. **Complete Issue #20 (Review Panel)** - 6 hours

### This Month:
4. **Write Issue #27 (Documentation)** - 4 hours
5. **Optional: Issue #26 (Admin Dashboard)** - 8 hours

---

## 📊 Current Project Health

### ✅ Completed:
- Phase 1-2: Security & Code Quality ✓
- Phase 3: v2 API Migration ✓
- Phase 5: UX & Navigation ✓ (except markdown)
- Phase 6: Mobile & Breadcrumbs ✓

### 🔄 In Progress:
- Phase 5: Enhanced Answers (1 issue remaining)

### 📋 Remaining:
- Phase 4: Content Moderation (2 issues)
- Phase 7: Admin Dashboard (1 issue)
- Phase 8: Documentation (1 issue)
- Phase 9: Advanced Admin (4 issues - deferred)

### 🎯 MVP Readiness:
**Current:** 85% complete
**After Issue #23:** 90% complete (MVP ready)
**After Issues #19-20:** 95% complete (Production ready)

---

## 💡 Strategic Recommendations

### For MVP Launch (Do These):
1. ✅ Issue #23 - Markdown Editor
2. ✅ Issue #19 - Profanity Filter
3. ✅ Issue #20 - Review Panel
4. ✅ Issue #27 - Documentation

**Rationale:** These complete core instructor/student features and provide adequate moderation tools for classroom use.

### For Post-Launch (Defer These):
1. ⏳ Issue #26 - Admin Dashboard
2. ⏳ Issues #29-32 - Phase 9 features

**Rationale:** Admin features are secondary to core user experience. Current admin functionality is sufficient for small-scale deployment.

### Maintenance:
- Keep Issue #13 open as help desk
- Monitor for bug reports
- Gather user feedback before building Phase 9 features

---

## 📞 Questions to Consider

Before starting development, consider:

1. **Is the demo at raisemyhand.hellmo.space ready for users?**
   - If yes, Issue #13 will generate requests
   - Need process for issuing API keys

2. **What's the target launch date?**
   - If soon: Focus on Issues #23, #19, #20 only
   - If flexible: Can include #27 and #26

3. **What's the expected user scale?**
   - Small (1-10 instructors): Current admin tools sufficient
   - Large (100+ instructors): Need Issue #26 (Admin Dashboard)

4. **Are there security/compliance requirements?**
   - If yes: Prioritize Issues #19-20 (profanity filter)
   - If educational institution: May need additional moderation

---

**Summary:** Start with Issue #23 (Markdown Editor), then complete Phase 4 (Issues #19-20). This gets the project to production-ready state. Admin dashboard and Phase 9 features can be deferred to post-launch based on user feedback.
