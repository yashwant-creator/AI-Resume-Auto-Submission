from pathlib import Path
import time
from typing import Dict, Optional, List
from playwright.sync_api import sync_playwright, Page
from datetime import datetime
import re


def _get_matched_attr(field_key: str, attr_values: Dict[str, str]) -> str:
    """
    Returns which attribute matched for debugging purposes.
    """
    key_map = {
        "name": [
            "name", "full name", "your name", "applicant_name", "applicant-name", 
            "first name", "last name", "fullname", "candidate name", "full_name",
            "firstname", "lastname", "first_name", "last_name"
        ],
        "email": [
            "email", "e-mail", "your email", "applicant_email", "contact email",
            "email address", "email_address", "emailaddress", "e_mail", "mail"
        ],
        "phone": [
            "phone", "phone number", "mobile", "telephone", "tel", "cell", "cellphone",
            "phone_number", "phonenumber", "contact number", "mobile number", 
            "cell phone", "contact_phone"
        ],
        "linkedin": [
            "linkedin", "linked in", "linkedin url", "linkedin profile",
            "linkedin_url", "profile_url"
        ],
        "website": [
            "website", "portfolio", "personal website", "web site", "url", "site"
        ],
    }
    checks = key_map.get(field_key, [])
    for attr_name, v in attr_values.items():
        if not v:
            continue
        low = v.lower()
        for c in checks:
            if c in low:
                return f"{attr_name}='{v}'"
    return "unknown"


def _match_input_for(field_key: str, attr_values: Dict[str, str]) -> bool:
    """
    Enhanced heuristic matcher to detect form fields by keyword matching.
    Checks common attribute patterns for name, email, phone, and other fields.
    """
    key_map = {
        "name": [
            "name", "full name", "your name", "applicant_name", "applicant-name", 
            "first name", "last name", "fullname", "candidate name", "full_name",
            "firstname", "lastname", "first_name", "last_name"
        ],
        "email": [
            "email", "e-mail", "your email", "applicant_email", "contact email",
            "email address", "email_address", "emailaddress", "e_mail", "mail"
        ],
        "phone": [
            "phone", "phone number", "mobile", "telephone", "tel", "cell", "cellphone",
            "phone_number", "phonenumber", "contact number", "mobile number", 
            "cell phone", "contact_phone"
        ],
        "linkedin": [
            "linkedin", "linked in", "linkedin url", "linkedin profile",
            "linkedin_url", "profile_url"
        ],
        "website": [
            "website", "portfolio", "personal website", "web site", "url", "site"
        ],
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
    Enhanced to include more attributes commonly used in modern ATS platforms.
    """
    attrs = {}
    try:
        # Core attributes
        for a in (
            "name", "id", "placeholder", "aria-label", "aria-labelledby",
            "aria-describedby", "class", "type", "data-test", "data-testid",
            "data-automation-id", "data-qa", "data-field-name", "data-field-id",
            "title", "alt", "autocomplete", "inputmode", "role",
            "data-name", "data-type", "data-field", "ng-model", "v-model",
            "formcontrolname", "data-bind", "data-cy", "data-selenium-id"
        ):
            attrs[a] = elem.get_attribute(a) or ""
        
        # Try to get label text from associated label element
        try:
            label_for = elem.get_attribute("id")
            if label_for:
                # Find label that references this input
                label = elem.evaluate("el => document.querySelector(`label[for='${el.id}']`)")
                if label:
                    attrs["label-text"] = label.inner_text() or ""
        except Exception:
            pass
        
        # Try to get nearby text (parent or previous sibling label)
        try:
            parent_text = elem.evaluate("el => el.parentElement?.textContent || ''")
            if parent_text and len(parent_text.strip()) < 100:  # Avoid getting too much text
                attrs["parent-text"] = parent_text.strip()
        except Exception:
            pass
            
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
    timeout: int = 60
) -> Dict:
    """
    Enhanced job application automation for real ATS platforms (Greenhouse, Lever, Ashby, etc.).
    
    This function:
    1. Opens the job posting page in a headless browser
    2. Handles multiple page navigation and multi-step forms
    3. Detects and fills all common fields (name, email, phone, linkedin, etc.) using enhanced heuristics
    4. Uploads a resume PDF
    5. Handles dropdowns, radio buttons, and checkboxes
    6. Finds and clicks the submit/apply button
    7. Handles multi-step forms (continues to next steps automatically)
    8. Detects success or failure with multiple confirmation strategies
    
    Args:
        job_url: URL of the job posting page
        resume_path: File path to the resume PDF
        fields: Dict with keys like 'name', 'email', 'phone', 'linkedin', 'website' (values can be empty strings)
        headless: Whether to run browser in headless mode
        timeout: Page navigation timeout in seconds (increased default for ATS platforms)
    
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
        "fields_filled": {"name": False, "email": False, "phone": False, "resume": False, "linkedin": False, "website": False}
    }
    
    resume_file = Path(resume_path)
    if not resume_file.exists():
        result["notes"].append(f"resume file not found at {resume_path}")
        return result

    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless, args=['--disable-blink-features=AutomationControlled'])
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Navigate to job posting
            try:
                result["notes"].append(f"navigating to {job_url}")
                page.goto(job_url, timeout=timeout * 1000, wait_until="domcontentloaded")
                # Wait for page to be interactive
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception as e:
                result["notes"].append(f"navigation warning: {str(e)[:100]}")
                # Continue anyway - page might have loaded enough
            
            # Wait for forms to render
            time.sleep(2)
            
            # Handle multi-step forms (up to 5 steps)
            max_steps = 5
            for step in range(max_steps):
                result["notes"].append(f"processing form step {step + 1}")
                
                # Find and fill form fields
                _fill_form_fields(page, fields, result)
                
                # Upload resume (try on each step)
                _upload_resume(page, resume_file, result)
                
                # Handle consent checkboxes
                _handle_consent_checkboxes(page, result)
                
                # Click submit/continue/next button
                button_clicked = _click_submit_or_continue_button(page, result)
                
                if not button_clicked:
                    result["notes"].append(f"no continue/submit button found on step {step + 1}")
                    break
                
                # Wait for next page/step to load
                time.sleep(3)
                
                # Check if we're done (success page or no more forms)
                if _detect_success(page, result):
                    break
                
                # Check if there are more forms to fill
                inputs = page.query_selector_all("input:not([type=hidden]), textarea, select")
                visible_inputs = [inp for inp in inputs if _is_visible(inp)]
                if len(visible_inputs) == 0:
                    result["notes"].append("no more visible form fields - assuming completion")
                    break
            
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
    Enhanced form field filling for real ATS platforms.
    Handles text inputs, textareas, and selects.
    """
    # Get all form elements
    inputs = page.query_selector_all("input:not([type=hidden]):not([type=file]), textarea, select")
    
    for inp in inputs:
        attrs = _collect_attrs(inp)
        itype = attrs.get("type", "") or ""
        tag_name = inp.evaluate("el => el.tagName").lower()
        
        # Skip non-visible fields
        if not _is_visible(inp):
            continue
        
        try:
            # Check if field is already filled
            current_value = inp.input_value() if tag_name == "input" else inp.evaluate("el => el.value")
            if current_value and len(str(current_value).strip()) > 0:
                continue  # Skip already filled fields
        except Exception:
            pass
        
        try:
            # Try to match against known patterns
            field_types_to_check = ["name", "email", "phone", "linkedin", "website"]
            
            for field_key in field_types_to_check:
                # Skip if we've already filled this type of field (unless it's a multi-part name)
                if result["fields_filled"].get(field_key) and field_key != "name":
                    continue
                    
                if _match_input_for(field_key, attrs):
                    value = fields.get(field_key, "")
                    if value and value.strip():
                        # Handle select dropdowns
                        if tag_name == "select":
                            # Try to select by value or text
                            try:
                                inp.select_option(value)
                                result["fields_filled"][field_key] = True
                                result["notes"].append(f"selected {field_key} in dropdown")
                            except Exception:
                                result["notes"].append(f"couldn't select {field_key} in dropdown")
                        else:
                            # Fill text input or textarea
                            inp.click()  # Focus the field first
                            time.sleep(0.3)
                            inp.fill(value)
                            result["fields_filled"][field_key] = True
                            field_name = attrs.get('name', attrs.get('id', 'unknown'))
                            # Enhanced logging with attribute details for debugging
                            result["notes"].append(f"filled {field_key}: '{field_name}' (matched via: {_get_matched_attr(field_key, attrs)})")
                        break
        except Exception as e:
            result["notes"].append(f"error filling field: {str(e)[:50]}")
            continue


def _upload_resume(page: Page, resume_file: Path, result: Dict) -> None:
    """
    Enhanced resume upload handling for ATS platforms.
    Handles both visible and hidden file inputs, and clicks upload buttons if needed.
    """
    # Skip if already uploaded
    if result["fields_filled"]["resume"]:
        return
    
    file_inputs = page.query_selector_all('input[type="file"]')
    
    for fi in file_inputs:
        try:
            # Try to make file input visible if it's hidden (common in ATS)
            try:
                fi.evaluate("el => el.style.display = 'block'")
                fi.evaluate("el => el.style.opacity = '1'")
                fi.evaluate("el => el.style.visibility = 'visible'")
            except Exception:
                pass
            
            # Attempt upload
            fi.set_input_files(str(resume_file))
            result["fields_filled"]["resume"] = True
            result["notes"].append(f"uploaded resume: {resume_file.name}")
            
            # Wait a bit for upload to process
            time.sleep(1)
            return
        except Exception as e:
            result["notes"].append(f"error uploading to file input: {str(e)[:50]}")
            continue
    
    # If no file input found, look for upload buttons/links
    if not result["fields_filled"]["resume"]:
        upload_keywords = ["upload", "attach", "choose file", "browse", "select file", "add resume"]
        buttons = page.query_selector_all("button, a, label, div[role='button']")
        
        for btn in buttons:
            try:
                text = (btn.inner_text() or "").lower()
                if any(keyword in text for keyword in upload_keywords):
                    result["notes"].append(f"found upload trigger: '{text[:30]}'")
                    # Click might reveal file input
                    btn.click()
                    time.sleep(0.5)
                    # Try file inputs again
                    file_inputs = page.query_selector_all('input[type="file"]')
                    if file_inputs:
                        file_inputs[0].set_input_files(str(resume_file))
                        result["fields_filled"]["resume"] = True
                        result["notes"].append(f"uploaded resume after clicking: {resume_file.name}")
                        return
            except Exception:
                continue


def _handle_consent_checkboxes(page: Page, result: Dict) -> None:
    """
    Automatically check consent/agreement checkboxes commonly found in ATS forms.
    """
    consent_keywords = [
        "agree", "consent", "terms", "privacy", "policy", "understand",
        "acknowledge", "confirm", "accept", "data processing", "gdpr",
        "equal opportunity", "voluntary", "self-identify"
    ]
    
    checkboxes = page.query_selector_all('input[type="checkbox"]')
    
    for cb in checkboxes:
        try:
            if not _is_visible(cb):
                continue
            
            # Get associated label or nearby text
            label_text = ""
            try:
                label_id = cb.get_attribute("id")
                if label_id:
                    label = page.query_selector(f'label[for="{label_id}"]')
                    if label:
                        label_text = label.inner_text().lower()
            except Exception:
                pass
            
            # Check parent text if no label
            if not label_text:
                try:
                    parent = cb.evaluate_handle("el => el.parentElement")
                    label_text = parent.evaluate("el => el.textContent").lower()
                except Exception:
                    pass
            
            # Check if it's a consent checkbox and not checked
            if any(keyword in label_text for keyword in consent_keywords):
                try:
                    is_checked = cb.is_checked()
                    if not is_checked:
                        cb.check()
                        result["notes"].append(f"checked consent box: '{label_text[:50]}'")
                except Exception as e:
                    result["notes"].append(f"error checking consent box: {str(e)[:30]}")
        except Exception:
            continue


def _click_submit_or_continue_button(page: Page, result: Dict) -> bool:
    """
    Find and click submit, continue, or next button.
    Returns True if a button was clicked, False otherwise.
    """
    # Prioritized keywords (submit/apply first, then continue/next)
    submit_keywords = ["submit", "apply now", "apply", "send application", "complete application"]
    continue_keywords = ["continue", "next", "proceed", "save and continue", "next step"]
    all_keywords = submit_keywords + continue_keywords
    
    # Try buttons and inputs first
    buttons = page.query_selector_all("button, input[type=submit], input[type=button], div[role=button]")
    
    # First pass: look for exact submit/apply buttons
    for btn in buttons:
        try:
            if not _is_visible(btn):
                continue
            
            text = (btn.inner_text() or "").lower().strip()
            value = (btn.get_attribute("value") or "").lower().strip()
            aria_label = (btn.get_attribute("aria-label") or "").lower().strip()
            full_text = f"{text} {value} {aria_label}".lower()
            
            # Check for exact submit/apply matches first
            for keyword in submit_keywords:
                if keyword in full_text:
                    btn.click()
                    result["notes"].append(f"clicked submit button: '{text or value or aria_label}'")
                    return True
        except Exception:
            continue
    
    # Second pass: look for continue/next buttons
    for btn in buttons:
        try:
            if not _is_visible(btn):
                continue
            
            text = (btn.inner_text() or "").lower().strip()
            value = (btn.get_attribute("value") or "").lower().strip()
            aria_label = (btn.get_attribute("aria-label") or "").lower().strip()
            full_text = f"{text} {value} {aria_label}".lower()
            
            for keyword in continue_keywords:
                if keyword in full_text:
                    btn.click()
                    result["notes"].append(f"clicked continue button: '{text or value or aria_label}'")
                    return True
        except Exception:
            continue
    
    # Try links as fallback
    links = page.query_selector_all("a")
    for link in links:
        try:
            if not _is_visible(link):
                continue
            
            text = (link.inner_text() or "").lower().strip()
            if any(keyword in text for keyword in all_keywords):
                link.click()
                result["notes"].append(f"clicked link: '{text}'")
                return True
        except Exception:
            continue
    
    return False


def _detect_success(page: Page, result: Dict) -> bool:
    """
    Enhanced success detection for ATS platforms.
    Returns True if success is detected, False otherwise.
    """
    success_indicators = [
        "thank you",
        "application submitted",
        "we have received",
        "thank you for applying",
        "application complete",
        "successfully submitted",
        "success",
        "we'll be in touch",
        "we will review",
        "received your application",
        "application has been submitted",
        "you're all set",
        "confirmation",
        "we've received your application"
    ]
    
    # Check page content
    try:
        page_text = page.content().lower()
        for indicator in success_indicators:
            if indicator in page_text:
                result["status"] = "submitted"
                result["submitted_at"] = datetime.utcnow().isoformat() + "Z"
                result["notes"].append(f"success confirmed by page content: '{indicator}'")
                return True
    except Exception:
        pass
    
    # Check page title
    try:
        title = page.title().lower()
        title_indicators = ["thank you", "confirmation", "success", "submitted", "complete"]
        for indicator in title_indicators:
            if indicator in title:
                result["status"] = "submitted"
                result["submitted_at"] = datetime.utcnow().isoformat() + "Z"
                result["notes"].append(f"success confirmed by page title: '{title}'")
                return True
    except Exception:
        pass
    
    # Check URL for confirmation pages
    try:
        url = page.url.lower()
        url_indicators = ["confirmation", "thank", "success", "submitted", "complete"]
        for indicator in url_indicators:
            if indicator in url:
                result["status"] = "submitted"
                result["submitted_at"] = datetime.utcnow().isoformat() + "Z"
                result["notes"].append(f"success confirmed by URL: '{url}'")
                return True
    except Exception:
        pass
    
    # Check for success icons/images
    try:
        success_icons = page.query_selector_all('svg, img, i')
        for icon in success_icons:
            try:
                classes = icon.get_attribute("class") or ""
                alt = icon.get_attribute("alt") or ""
                combined = f"{classes} {alt}".lower()
                if "check" in combined or "success" in combined or "confirm" in combined:
                    result["status"] = "submitted"
                    result["submitted_at"] = datetime.utcnow().isoformat() + "Z"
                    result["notes"].append("success confirmed by success icon")
                    return True
            except Exception:
                continue
    except Exception:
        pass
    
    return False
