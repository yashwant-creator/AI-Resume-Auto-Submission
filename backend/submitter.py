from pathlib import Path
import time
from typing import Dict, Optional, List
from playwright.sync_api import sync_playwright, Page
from datetime import datetime


def _match_input_for(field_key: str, attr_values: Dict[str, str]) -> bool:
    """
    Heuristic matcher to detect form fields by keyword matching.
    Checks common attribute patterns for name, email, and phone fields.
    """
    key_map = {
        "name": ["name", "full name", "your name", "applicant_name", "applicant-name", "first name", "last name"],
        "email": ["email", "e-mail", "your email", "applicant_email", "contact email"],
        "phone": ["phone", "phone number", "mobile", "telephone", "tel", "cell", "cellphone"],
    }
    checks = key_map.get(field_key, [])
    for v in attr_values.values():
        if not v:
            continue
        low = v.lower()
        for c in checks:
            if c in low:
                return True
    return False


def _collect_attrs(elem) -> Dict[str, str]:
    """
    Collect relevant attributes from a DOM element for inspection.
    """
    attrs = {}
    try:
        for a in ("name", "id", "placeholder", "aria-label", "class", "type", "data-test"):
            attrs[a] = elem.get_attribute(a) or ""
    except Exception:
        pass
    return attrs


def _is_visible(elem) -> bool:
    """
    Check if an element is visible on the page.
    """
    try:
        return elem.is_visible()
    except Exception:
        return False


def submit_application(
    job_url: str, 
    resume_path: str, 
    fields: Dict[str, str], 
    headless: bool = True, 
    timeout: int = 30
) -> Dict:
    """
    Attempt to open a job posting URL and auto-fill basic application fields.
    
    This function:
    1. Opens the job posting page in a headless browser
    2. Detects and fills basic fields (name, email, phone) using heuristics
    3. Uploads a resume PDF
    4. Finds and clicks the submit/apply button
    5. Detects success or failure
    
    Args:
        job_url: URL of the job posting page
        resume_path: File path to the resume PDF
        fields: Dict with keys 'name', 'email', 'phone' (values can be empty strings)
        headless: Whether to run browser in headless mode
        timeout: Page navigation timeout in seconds
    
    Returns:
        Dict with keys:
        - job_url: The input job URL
        - status: 'submitted', 'failed', or 'error'
        - submitted_at: ISO timestamp if successfully submitted
        - notes: List of execution details for debugging
        - fields_filled: Dict showing which fields were successfully filled
    """
    result = {
        "job_url": job_url, 
        "status": "failed", 
        "submitted_at": None, 
        "notes": [],
        "fields_filled": {"name": False, "email": False, "phone": False, "resume": False}
    }
    
    resume_file = Path(resume_path)
    if not resume_file.exists():
        result["notes"].append(f"resume file not found at {resume_path}")
        return result

    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            # Navigate to job posting
            try:
                result["notes"].append(f"navigating to {job_url}")
                page.goto(job_url, timeout=timeout * 1000, wait_until="networkidle")
            except Exception as e:
                result["notes"].append(f"failed to navigate: {str(e)[:100]}")
                return result

            # Find and fill form fields
            _fill_form_fields(page, fields, result)
            
            # Upload resume
            _upload_resume(page, resume_file, result)
            
            # Click submit button
            _click_submit_button(page, result)
            
            # Wait for page to process
            time.sleep(2)
            
            # Check for success indicators
            _detect_success(page, result)
            
            browser.close()

    except Exception as e:
        result["status"] = "error"
        result["notes"].append(f"unexpected error: {str(e)[:100]}")
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass

    return result


def _fill_form_fields(page: Page, fields: Dict[str, str], result: Dict) -> None:
    """
    Attempt to find and fill name, email, and phone fields on the form.
    """
    inputs = page.query_selector_all("input, textarea")
    
    for inp in inputs:
        attrs = _collect_attrs(inp)
        itype = attrs.get("type", "") or ""
        
        # Skip file inputs and non-visible fields
        if itype == "file" or not _is_visible(inp):
            continue
        
        try:
            # Try to match against known patterns
            for field_key in ("name", "email", "phone"):
                if result["fields_filled"][field_key]:
                    continue
                    
                if _match_input_for(field_key, attrs):
                    value = fields.get(field_key, "")
                    if value:
                        inp.fill(value)
                        result["fields_filled"][field_key] = True
                        result["notes"].append(f"filled {field_key}: '{attrs.get('name', attrs.get('id', 'unknown'))}'")
                        break
        except Exception as e:
            result["notes"].append(f"error filling field: {str(e)[:50]}")
            continue


def _upload_resume(page: Page, resume_file: Path, result: Dict) -> None:
    """
    Attempt to upload the resume PDF to the first available file input.
    """
    file_inputs = page.query_selector_all('input[type="file"]')
    
    for fi in file_inputs:
        try:
            if _is_visible(fi):
                fi.set_input_files(str(resume_file))
                result["fields_filled"]["resume"] = True
                result["notes"].append(f"uploaded resume: {resume_file.name}")
                return
        except Exception as e:
            result["notes"].append(f"error uploading to file input: {str(e)[:50]}")
            continue


def _click_submit_button(page: Page, result: Dict) -> None:
    """
    Find and click the submit/apply button.
    """
    submit_keywords = ["submit", "apply", "send", "send application", "complete application", "continue"]
    
    # Try buttons first
    buttons = page.query_selector_all("button, input[type=submit]")
    for btn in buttons:
        try:
            if not _is_visible(btn):
                continue
            
            text = (btn.inner_text() or "").lower()
            value = (btn.get_attribute("value") or "").lower()
            full_text = f"{text} {value}".lower()
            
            if any(keyword in full_text for keyword in submit_keywords):
                btn.click()
                result["notes"].append(f"clicked button: '{text or value}'")
                return
        except Exception:
            continue
    
    # Try links as fallback
    links = page.query_selector_all("a")
    for link in links:
        try:
            if not _is_visible(link):
                continue
            
            text = (link.inner_text() or "").lower()
            if any(keyword in text for keyword in submit_keywords):
                link.click()
                result["notes"].append(f"clicked link: '{text}'")
                return
        except Exception:
            continue
    
    result["notes"].append("no submit button found")


def _detect_success(page: Page, result: Dict) -> None:
    """
    Attempt to detect if the application was successfully submitted.
    """
    success_indicators = [
        "thank you",
        "application submitted",
        "we have received",
        "thank you for applying",
        "application complete",
        "successfully submitted",
        "success",
    ]
    
    try:
        page_text = page.content().lower()
        if any(indicator in page_text for indicator in success_indicators):
            result["status"] = "submitted"
            result["submitted_at"] = datetime.utcnow().isoformat() + "Z"
            result["notes"].append("success confirmed by page content")
            return
    except Exception:
        pass
    
    # If we clicked a submit button, assume success
    if any("clicked button" in note or "clicked link" in note for note in result["notes"]):
        result["status"] = "submitted"
        result["submitted_at"] = datetime.utcnow().isoformat() + "Z"
        result["notes"].append("submit button was clicked (assumed success)")
        return
    
    result["notes"].append("could not confirm success")
