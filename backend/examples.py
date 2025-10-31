#!/usr/bin/env python3
"""
Example: Using the submitter module directly in Python.

This shows how to import and use the submitter module programmatically
instead of through the API.
"""

from pathlib import Path
from submitter import submit_application


def example_1_single_submission():
    """Submit a single application."""
    print("Example 1: Single Application Submission")
    print("=" * 50)
    
    job_url = "https://example.greenhouse.io/jobs/123456"
    resume_path = "path/to/your/resume.pdf"
    
    fields = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234"
    }
    
    result = submit_application(
        job_url=job_url,
        resume_path=resume_path,
        fields=fields,
        headless=True,
        timeout=30
    )
    
    print(f"Status: {result['status']}")
    print(f"Submitted at: {result['submitted_at']}")
    print(f"Fields filled: {result['fields_filled']}")
    print(f"Notes: {result['notes']}")
    
    return result


def example_2_with_logging():
    """Submit with detailed logging."""
    print("\nExample 2: Submission with Logging")
    print("=" * 50)
    
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    job_url = "https://example.ashby.io/jobs/789012"
    resume_path = "path/to/your/resume.pdf"
    
    fields = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": ""  # Optional
    }
    
    logger.info(f"Starting submission for {job_url}")
    
    result = submit_application(
        job_url=job_url,
        resume_path=resume_path,
        fields=fields,
        headless=False,  # Show browser window
        timeout=60
    )
    
    logger.info(f"Submission complete: {result['status']}")
    
    return result


def example_3_error_handling():
    """Handle errors gracefully."""
    print("\nExample 3: Error Handling")
    print("=" * 50)
    
    job_url = "https://example.com/not-a-real-job"
    resume_path = "nonexistent_resume.pdf"
    
    fields = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "555-5555"
    }
    
    try:
        result = submit_application(
            job_url=job_url,
            resume_path=resume_path,
            fields=fields,
            headless=True
        )
        
        if result['status'] == 'error':
            print(f"❌ Error: {result['notes']}")
        elif result['status'] == 'failed':
            print(f"⚠️ Failed: Check notes for details")
            print(f"Notes: {result['notes']}")
        else:
            print(f"✅ Success: {result['submitted_at']}")
    
    except Exception as e:
        print(f"❌ Exception: {e}")


def example_4_batch_processing():
    """Process multiple applications."""
    print("\nExample 4: Batch Processing")
    print("=" * 50)
    
    jobs = [
        {"url": "https://example1.greenhouse.io/jobs/111"},
        {"url": "https://example2.greenhouse.io/jobs/222"},
        {"url": "https://example3.greenhouse.io/jobs/333"},
    ]
    
    resume_path = "path/to/your/resume.pdf"
    fields = {
        "name": "Batch Test",
        "email": "batch@example.com",
        "phone": "555-0000"
    }
    
    results = []
    for idx, job in enumerate(jobs, 1):
        print(f"\n[{idx}/{len(jobs)}] Processing: {job['url']}")
        
        result = submit_application(
            job_url=job['url'],
            resume_path=resume_path,
            fields=fields,
            headless=True
        )
        
        results.append(result)
        
        # Print status
        status_symbol = "✅" if result['status'] == 'submitted' else "❌"
        print(f"{status_symbol} Status: {result['status']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    submitted = sum(1 for r in results if r['status'] == 'submitted')
    failed = sum(1 for r in results if r['status'] == 'failed')
    errors = sum(1 for r in results if r['status'] == 'error')
    
    print(f"✅ Submitted: {submitted}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Errors: {errors}")
    print(f"📊 Total: {len(jobs)}")


def example_5_minimal():
    """Minimal example - only required fields."""
    print("\nExample 5: Minimal Submission")
    print("=" * 50)
    
    result = submit_application(
        job_url="https://example.greenhouse.io/jobs/999",
        resume_path="resume.pdf",
        fields={"name": "", "email": "", "phone": ""}
    )
    
    print(f"Result: {result}")


if __name__ == "__main__":
    # Run examples (uncomment to test)
    
    # example_1_single_submission()
    # example_2_with_logging()
    # example_3_error_handling()
    # example_4_batch_processing()
    # example_5_minimal()
    
    print("📝 Uncomment examples in this script to run them")
    print("   Each example demonstrates different usage patterns")
