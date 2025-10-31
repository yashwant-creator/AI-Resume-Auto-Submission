#!/usr/bin/env python3
"""
Batch submission script for multiple job applications.

Usage:
    python3 batch_submit.py jobs.json resume.pdf --name "John Doe" --email "john@example.com" --phone "555-1234"

jobs.json format:
[
  {"url": "https://greenhouse.io/..."},
  {"url": "https://ashby.io/..."},
  ...
]
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from submitter import submit_application


def load_jobs(file_path: str) -> list:
    """Load job URLs from JSON file."""
    with open(file_path, 'r') as f:
        jobs = json.load(f)
    
    if not isinstance(jobs, list):
        raise ValueError("jobs.json must contain an array of job objects")
    
    return jobs


def main():
    parser = argparse.ArgumentParser(
        description="Batch submit job applications with resume"
    )
    parser.add_argument(
        "jobs_file",
        help="JSON file with job URLs: [{\"url\": \"https://...\"}, ...]"
    )
    parser.add_argument(
        "resume",
        help="Path to resume PDF file"
    )
    parser.add_argument(
        "--name",
        default="",
        help="Your full name (optional)"
    )
    parser.add_argument(
        "--email",
        default="",
        help="Your email address (optional)"
    )
    parser.add_argument(
        "--phone",
        default="",
        help="Your phone number (optional)"
    )
    parser.add_argument(
        "--output",
        default="submissions.json",
        help="Output file for results (default: submissions.json)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)"
    )
    
    args = parser.parse_args()
    
    # Validate files
    if not Path(args.jobs_file).exists():
        print(f"❌ Jobs file not found: {args.jobs_file}")
        sys.exit(1)
    
    if not Path(args.resume).exists():
        print(f"❌ Resume file not found: {args.resume}")
        sys.exit(1)
    
    # Load jobs
    try:
        jobs = load_jobs(args.jobs_file)
    except Exception as e:
        print(f"❌ Error loading jobs: {e}")
        sys.exit(1)
    
    if not jobs:
        print("❌ No jobs found in file")
        sys.exit(1)
    
    print(f"📋 Found {len(jobs)} job(s) to process")
    print(f"📄 Resume: {args.resume}")
    print(f"👤 Name: {args.name or '(not provided)'}")
    print(f"📧 Email: {args.email or '(not provided)'}")
    print(f"📞 Phone: {args.phone or '(not provided)'}")
    print()
    
    fields = {
        "name": args.name,
        "email": args.email,
        "phone": args.phone
    }
    
    results = {
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "total": len(jobs),
        "submissions": []
    }
    
    submitted_count = 0
    failed_count = 0
    error_count = 0
    
    for idx, job in enumerate(jobs, 1):
        job_url = job.get("url")
        if not job_url:
            print(f"⚠️  Job {idx}: Missing 'url' field")
            continue
        
        print(f"[{idx}/{len(jobs)}] Processing: {job_url[:60]}...")
        
        try:
            result = submit_application(
                job_url=job_url,
                resume_path=args.resume,
                fields=fields,
                headless=args.headless
            )
            
            results["submissions"].append(result)
            
            if result["status"] == "submitted":
                print(f"  ✅ Submitted")
                submitted_count += 1
            elif result["status"] == "failed":
                print(f"  ❌ Failed")
                failed_count += 1
            else:
                print(f"  ⚠️  Error")
                error_count += 1
        
        except Exception as e:
            print(f"  ⚠️  Exception: {str(e)[:50]}")
            error_count += 1
            results["submissions"].append({
                "job_url": job_url,
                "status": "error",
                "submitted_at": None,
                "notes": [str(e)]
            })
    
    # Summary
    print()
    print("=" * 50)
    print("📊 Summary")
    print("=" * 50)
    print(f"✅ Submitted: {submitted_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⚠️  Errors: {error_count}")
    print(f"📝 Total: {len(jobs)}")
    print()
    
    # Save results
    results["stats"] = {
        "submitted": submitted_count,
        "failed": failed_count,
        "error": error_count,
        "total": len(jobs)
    }
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"💾 Results saved to: {args.output}")
    
    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
