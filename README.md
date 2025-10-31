# AI Resume Auto-Submission 🤖

A simple, effective automation tool that fills out job application forms and submits your resume in seconds.

**Built for:** Greenhouse, Ashby, and similar ATS platforms  
**Tech Stack:** Python (FastAPI + Playwright) + React (Vite)  
**Time to Deploy:** 5 minutes

---

## 📋 Overview

This tool automates the tedious parts of job applications:

1. ✅ Navigates to a job posting URL
2. ✅ Detects and fills form fields (name, email, phone)
3. ✅ Uploads your resume PDF
4. ✅ Clicks the submit button
5. ✅ Returns a detailed JSON log with success/failure status

**Output Example:**
```json
{
  "job_url": "https://greenhouse.io/...",
  "status": "submitted",
  "submitted_at": "2025-10-30T14:23:45Z",
  "fields_filled": {
    "name": true,
    "email": true,
    "phone": true,
    "resume": true
  },
  "notes": [
    "navigating to https://greenhouse.io/...",
    "filled name: 'name'",
    "filled email: 'email'",
    "uploaded resume: resume.pdf",
    "clicked button: 'apply now'",
    "success confirmed by page content"
  ]
}
```

---

## 🚀 Quick Start (macOS/Linux)

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### 1️⃣ Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (one-time)
playwright install chromium

# Start backend server
uvicorn main:app --reload --port 8001
```

Backend will be available at: `http://localhost:8001`

### 2️⃣ Frontend Setup

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
VITE_BACKEND_URL=http://localhost:8001 npm run dev
```

Frontend will be available at: `http://localhost:5173`

### 3️⃣ Use the Application

1. Open `http://localhost:5173` in your browser
2. Paste a job posting URL (e.g., from Greenhouse or Ashby)
3. Upload your resume PDF
4. (Optional) Enter your name, email, and phone
5. Click **Submit Application**
6. Check the results in the "Application Log" section

---

## 📦 Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI server
│   ├── submitter.py         # Playwright automation logic
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # React component
│   │   ├── main.jsx         # Entry point
│   │   └── styles.css       # Styling
│   ├── package.json
│   ├── index.html
│   └── vite.config.js
└── README.md
```

---

## 🔧 API Endpoint

### `POST /submit`

**Request (multipart/form-data):**
```
job_url: string (required) - URL of the job posting
resume: file (required)    - PDF resume file
name: string (optional)    - Applicant name
email: string (optional)   - Applicant email
phone: string (optional)   - Applicant phone
```

**Response (200 OK):**
```json
{
  "job_url": "https://...",
  "status": "submitted|failed|error",
  "submitted_at": "2025-10-30T14:23:45Z",
  "notes": ["log entry 1", "log entry 2"],
  "fields_filled": {"name": true, "email": true, "phone": true, "resume": true}
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8001/submit \
  -F "job_url=https://greenhouse.io/..." \
  -F "resume=@/path/to/resume.pdf" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "phone=555-1234"
```

---

## 🎯 How It Works

### Form Field Detection

The tool uses **heuristic matching** to identify form fields:

- **Name**: Looks for attributes containing "name", "full name", "your name", etc.
- **Email**: Looks for attributes containing "email", "e-mail", etc.
- **Phone**: Looks for attributes containing "phone", "mobile", "tel", etc.

### Resume Upload

- Detects `<input type="file">` elements
- Uploads the provided PDF to the first visible file input
- Falls back to any available file input if needed

### Submit Detection

- Looks for buttons/links with text like "apply", "submit", "send application"
- Checks page content for success messages ("thank you", "submitted", etc.)
- Returns success status based on either confirmation message or button click

---

## ⚠️ Limitations & Considerations

1. **ATS Variation**: This tool works best with standard Greenhouse/Ashby forms. Custom-built job boards may not be compatible.

2. **JavaScript-Heavy Sites**: If a site heavily relies on client-side JavaScript for validation, the tool may not detect all fields.

3. **CAPTCHA & Security**: If a site requires CAPTCHA or has advanced bot detection, submission will fail. This is intentional (respects site ToS).

4. **Required Fields**: If the form requires fields beyond name/email/phone (e.g., "years of experience"), the automation will submit with those fields empty.

5. **Session Management**: Each submission starts a new browser session. No cookies or session state is preserved.

---

## 🛠️ Development

### Adding Support for More Fields

Edit `backend/submitter.py` and update `_match_input_for()`:

```python
key_map = {
    "name": ["name", "full name", ...],
    "email": ["email", ...],
    "phone": ["phone", ...],
    "linkedin": ["linkedin", "linkedin url", ...],  # Add new field
}
```

Then update the form in `frontend/src/App.jsx` to accept the new field.

### Testing with Playwright Inspector

```bash
# Run browser in headed mode (visible window)
cd backend
python3 -c "
from submitter import submit_application
result = submit_application(
    'https://example.com/jobs',
    '/path/to/resume.pdf',
    {'name': 'Test', 'email': 'test@example.com', 'phone': '555-1234'},
    headless=False  # Show browser
)
print(result)
"
```

---

## 📊 Response Status Values

| Status | Meaning |
|--------|---------|
| `submitted` | Application was successfully submitted |
| `failed` | Form was found but submission likely failed |
| `error` | Server or connection error occurred |

Check the `notes` array for detailed debugging information.

---

## 🔒 Privacy & Security

- ✅ All processing happens locally (your PC runs the browser)
- ✅ Resume never sent to any service except the target ATS
- ✅ No data stored on servers
- ✅ No tracking or analytics

---

## 📝 Example Workflow

```bash
# 1. Find a job on Greenhouse
# Example: https://example.greenhouse.io/jobs/123456

# 2. Copy the URL

# 3. Open the app at http://localhost:5173

# 4. Paste URL, upload resume, fill optional fields

# 5. Click Submit

# 6. Check results in the JSON log
```

---

## 🐛 Troubleshooting

### "Module not found: playwright"
```bash
cd backend
pip install playwright
playwright install chromium
```

### Frontend can't connect to backend
- Check that backend is running: `http://localhost:8001/health`
- Verify `VITE_BACKEND_URL` is set correctly
- Check browser console for CORS errors

### Browser fails to open URL
- Verify URL is correct and publicly accessible
- Check if site requires login
- Try the URL manually in a regular browser first

### Resume not uploading
- Ensure file is valid PDF
- Check browser console for JavaScript errors
- Try submitting manually to verify form works

---

## 📦 Dependencies

**Backend:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `playwright` - Browser automation
- `python-multipart` - Form data handling

**Frontend:**
- `react` - UI framework
- `vite` - Build tool

---

## 📄 License

This project is provided as-is for educational purposes.

---

## 💡 Tips for Best Results

1. **Test First**: Try the job posting manually to ensure it works
2. **Standard Fields**: Sites with standard form fields work best
3. **Wait Time**: Some sites take a few seconds to process submissions—the tool waits 2s
4. **Feedback**: Check the execution notes to debug any issues
5. **Batch Mode**: To submit multiple applications, repeat the process or build a batch script

---

**Questions?** Check the notes in the application log for detailed execution information!

## Output sample

```json
{
  "job_url": "https://...",
  "status": "submitted",
  "submitted_at": "2025-09-23T12:00:00Z",
  "notes": ["filled email", "uploaded resume to file input", "clicked button with text 'apply'"]
}
```

## Notes & limitations
- The submitter uses heuristics and may not fill every site. It's intended as a simple demo.
- Playwright must have browsers installed (see `playwright install chromium`).
- Use a test job posting (or your own test page) to validate behavior before using on production sites.

If you want, I can: add better selectors for Greenhouse specifically, add unit tests for the backend, or run a test with a sample JD & resume you provide.
