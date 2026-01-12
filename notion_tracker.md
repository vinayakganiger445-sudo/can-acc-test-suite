# 📅 ACC CAN Test Suite - Progress Tracker

> Copy this to your Notion page. Use the checkboxes to track daily progress.

---

## 🎯 Project Overview

**Goal:** Build a complete CAN test suite for Adaptive Cruise Control validation  
**Duration:** 4 weeks  
**Tech Stack:** Python, pytest, cantools, pandas, Plotly

---

## 📊 Weekly Milestones

### Week 1: Foundation (Parsing + 2 Tests)

#### Monday
- [ ] Set up project directory structure
- [ ] Create virtual environment
- [ ] Install dependencies from `requirements.txt`
- **Learnings:** _____________________

#### Tuesday
- [ ] Study ASC log format specification
- [ ] Implement `parse_asc_line()` function
- [ ] Test parsing with sample data
- **Learnings:** _____________________

#### Wednesday
- [ ] Study DBC file format
- [ ] Implement `load_dbc()` function
- [ ] Implement `decode_signals()` function
- **Learnings:** _____________________

#### Thursday
- [ ] Write overspeed test case
- [ ] Configure speed threshold (100 km/h)
- [ ] Verify detection in sample log
- **Learnings:** _____________________

#### Friday
- [ ] Write timeout test case
- [ ] Configure timeout threshold (2s)
- [ ] Test interval calculation
- **Learnings:** _____________________

#### Weekend Review
- [ ] Review Week 1 code
- [ ] Document any issues
- [ ] Prepare Week 2 priorities

---

### Week 2: Complete Test Suite

#### Monday
- [ ] Implement emergency stop detection
- [ ] Calculate deceleration rate
- [ ] Combine brake + speed criteria
- **Learnings:** _____________________

#### Tuesday
- [ ] Implement signal bounds validation
- [ ] Extract limits from DBC
- [ ] Handle edge cases
- **Learnings:** _____________________

#### Wednesday
- [ ] Implement checksum validation
- [ ] Study XOR checksum algorithm
- [ ] Test with valid/invalid data
- **Learnings:** _____________________

#### Thursday
- [ ] Create pytest test file
- [ ] Implement fixtures for data loading
- [ ] Add parametrized tests
- **Learnings:** _____________________

#### Friday
- [ ] Run full test suite
- [ ] Fix any failing tests
- [ ] Check coverage percentage
- **Learnings:** _____________________

#### Weekend Review
- [ ] All 5 test cases working
- [ ] Coverage > 60%
- [ ] Document test results

---

### Week 3: Dashboard + Visualization

#### Monday
- [ ] Study Plotly graph objects
- [ ] Create speed timeline plot
- [ ] Add threshold lines
- **Learnings:** _____________________

#### Tuesday
- [ ] Create throttle timeline plot
- [ ] Create brake timeline plot
- [ ] Style plots consistently
- **Learnings:** _____________________

#### Wednesday
- [ ] Add violation markers
- [ ] Implement hover tooltips
- [ ] Add test summary bar chart
- **Learnings:** _____________________

#### Thursday
- [ ] Create subplot layout
- [ ] Add dashboard title/annotations
- [ ] Export to HTML
- **Learnings:** _____________________

#### Friday
- [ ] Test dashboard in browser
- [ ] Verify all interactive features
- [ ] Optimize performance
- **Learnings:** _____________________

#### Weekend Review
- [ ] Dashboard fully functional
- [ ] Interactive features working
- [ ] Visually polished

---

### Week 4: Polish + Documentation

#### Monday
- [ ] Write README overview
- [ ] Add setup instructions
- [ ] Add architecture diagram
- **Learnings:** _____________________

#### Tuesday
- [ ] Create run_all.py script
- [ ] Add command-line arguments
- [ ] Test full pipeline
- **Learnings:** _____________________

#### Wednesday
- [ ] Run coverage report
- [ ] Add tests to reach 80%+
- [ ] Fix any edge cases
- **Learnings:** _____________________

#### Thursday
- [ ] Initialize git repository
- [ ] Make initial commit
- [ ] Create GitHub repository
- **Learnings:** _____________________

#### Friday
- [ ] Final code review
- [ ] Update all docstrings
- [ ] Prepare portfolio presentation
- **Learnings:** _____________________

#### Weekend Review
- [ ] Project complete!
- [ ] Coverage ≥ 80%
- [ ] Ready for recruiter review

---

## 📈 Key Metrics Tracking

| Metric | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|--------|--------|--------|--------|
| Tests Passing | /2 | /5 | /5 | /5 |
| Coverage % | | | | ≥80% |
| Commits | | | | |
| Learning Hours | | | | |

---

## 📝 Daily Log Template

### Date: ___________

**Completed Today:**
- 

**Blockers/Issues:**
- 

**Tomorrow's Plan:**
- 

**Key Learning:**
- 

---

## 🔗 Quick Commands Reference

```powershell
# Activate environment
.\venv\Scripts\activate

# Run tests with coverage
pytest test_acc.py -v --cov=. --cov-report=html

# Generate dashboard
python dashboard.py

# Run full pipeline
python run_all.py

# View coverage report
start htmlcov\index.html
```

---

## 🏆 Success Criteria Checklist

- [ ] All 5 test cases implemented and passing
- [ ] Code coverage ≥ 80%
- [ ] Interactive dashboard generated
- [ ] README complete with setup instructions
- [ ] Git repository with clean commit history
- [ ] No linting errors
- [ ] All docstrings complete
- [ ] Ready for portfolio showcase

---

*Last Updated: January 12, 2026*
