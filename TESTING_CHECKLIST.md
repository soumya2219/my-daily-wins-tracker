# Testing Checklist & Quick Reference

## 📋 What You Need To Do

### 1. HTML Validation (9 pages)
**Tool:** https://validator.w3.org/#validate_by_input

**Pages to validate:**
- [ ] Home page (logged out): http://127.0.0.1:8080/
- [ ] Home page (logged in): http://127.0.0.1:8080/ (after login)
- [ ] Registration: http://127.0.0.1:8080/register/
- [ ] Login: http://127.0.0.1:8080/login/
- [ ] Dashboard: http://127.0.0.1:8080/weekly/
- [ ] Entry List: http://127.0.0.1:8080/entries/
- [ ] Entry Detail: http://127.0.0.1:8080/entries/1/ (pick any entry ID)
- [ ] Categories: http://127.0.0.1:8080/categories/
- [ ] 404 page: http://127.0.0.1:8080/404/

**Steps for each page:**
1. Open page in browser
2. Right-click → View Page Source
3. Ctrl+A (select all) → Ctrl+C (copy)
4. Go to https://validator.w3.org/#validate_by_input
5. Paste HTML
6. Click "Check"
7. Take screenshot
8. Save as: `documentation/testing/html/[pagename].png`

---

### 2. CSS Validation (3 files)
**Tool:** https://jigsaw.w3.org/css-validator/#validate_by_input

**Files to validate:**
- [ ] static/css/base.css
- [ ] static/css/home.css
- [ ] static/css/weekly_dashboard.css

**Steps for each file:**
1. Open the CSS file in VS Code
2. Ctrl+A (select all) → Ctrl+C (copy)
3. Go to https://jigsaw.w3.org/css-validator/#validate_by_input
4. Paste CSS
5. Click "Check"
6. Take screenshot of results
7. Take screenshot of warnings (if any)
8. Save as: `documentation/testing/css/[filename].png`

---

### 3. JavaScript Validation (1 file)
**Tool:** https://jshint.com/

**File to validate:**
- [ ] static/js/weekly_dashboard.js

**Steps:**
1. Open static/js/weekly_dashboard.js
2. Ctrl+A → Ctrl+C
3. Go to https://jshint.com/
4. Paste code
5. Click "Configure" (top right):
   - Check "New JavaScript features (ES6)"
   - Add to "Assume" section: `$, bootstrap, document, window, fetch, FormData`
6. Take screenshot
7. Save as: `documentation/testing/js/dashboard.png`

---

### 4. Python Validation (14 files)
**Tool:** https://pep8ci.herokuapp.com/

**Files to validate:**

**Config App:**
- [ ] config/settings.py
- [ ] config/urls.py
- [ ] config/wsgi.py
- [ ] config/asgi.py

**Tracker App:**
- [ ] tracker/models.py
- [ ] tracker/views.py
- [ ] tracker/forms.py
- [ ] tracker/urls.py
- [ ] tracker/admin.py
- [ ] tracker/validators.py
- [ ] tracker/auth_forms.py
- [ ] tracker/apps.py
- [ ] tracker/templatetags/win_filters.py
- [ ] manage.py

**Steps for each file:**
1. Open file in VS Code
2. Ctrl+A → Ctrl+C
3. Go to https://pep8ci.herokuapp.com/
4. Paste code
5. Click "Check"
6. Take screenshot
7. Save as: `documentation/testing/python/[appname]_[filename].png`
   Example: `tracker_models.png`, `config_settings.png`

---

### 5. Lighthouse Testing (8 pages × 2 modes = 16 tests)
**Tool:** Chrome DevTools

**Pages to test:**
- [ ] Home page (Desktop)
- [ ] Home page (Mobile)
- [ ] Registration (Desktop)
- [ ] Registration (Mobile)
- [ ] Login (Desktop)
- [ ] Login (Mobile)
- [ ] Dashboard (Desktop)
- [ ] Dashboard (Mobile)
- [ ] Entry List (Desktop)
- [ ] Entry List (Mobile)
- [ ] Entry Detail (Desktop)
- [ ] Entry Detail (Mobile)
- [ ] Categories (Desktop)
- [ ] Categories (Mobile)
- [ ] 404 page (Desktop)
- [ ] 404 page (Mobile)

**Steps for each page:**
1. Open page in Chrome
2. Press F12 (open DevTools)
3. Click "Lighthouse" tab
4. Select mode (Desktop or Mobile)
5. Check all categories
6. Click "Analyze page load"
7. Wait for results
8. Take screenshot
9. Save as: `documentation/testing/lighthouse/[pagename]_[desktop|mobile].png`

---

### 6. Responsiveness Screenshots
**Tool:** Chrome DevTools responsive mode

**Steps:**
1. Open a page
2. F12 → Click device toolbar icon (Ctrl+Shift+M)
3. Test different sizes: 375px, 768px, 1024px, 1920px
4. Take screenshots showing layout at each size
5. Save in: `documentation/testing/responsiveness/`

---

### 7. Browser Compatibility Screenshots
**Browsers to test:**
- [ ] Chrome (your main browser - just screenshot)
- [ ] Firefox (download if needed)
- [ ] Edge (built into Windows)
- [ ] Safari (if you have Mac/iPhone)

**Steps:**
1. Open your Heroku site in each browser
2. Test main features
3. Take screenshots
4. Save in: `documentation/testing/browser/`

---

## 🎯 Priority Order

**Do these FIRST (most important):**
1. ✅ HTML Validation (9 pages) - 30 minutes
2. ✅ Python Validation (14 files) - 45 minutes
3. ✅ CSS Validation (3 files) - 15 minutes
4. ✅ JavaScript Validation (1 file) - 5 minutes

**Do these SECOND:**
5. ✅ Lighthouse Desktop (8 pages) - 30 minutes
6. ✅ Lighthouse Mobile (8 pages) - 30 minutes

**Do these LAST (if time):**
7. ✅ Responsiveness screenshots - 20 minutes
8. ✅ Browser screenshots - 15 minutes

---

## 💾 After Each Batch

When you finish a section:
1. Let me know what you found
2. Share any errors/warnings
3. I'll help you fix issues if needed
4. I'll update TESTING.md with your results

---

## ⚡ Quick Links

- W3C HTML: https://validator.w3.org/#validate_by_input
- W3C CSS: https://jigsaw.w3.org/css-validator/#validate_by_input
- JSHint: https://jshint.com/
- PEP8: https://pep8ci.herokuapp.com/
- Local server: http://127.0.0.1:8080/

---

**Ready to start?** Begin with HTML validation - it's the easiest! 🚀
