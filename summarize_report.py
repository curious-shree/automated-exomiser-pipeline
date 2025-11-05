import re

def summarize_verification_report(report_file):
    """
    Parses a verification report file and prints a concise summary.
    """
    passed_files = []
    failed_files = {}
    total_files = 0
    
    with open(report_file, 'r') as f:
        content = f.read()

    # Split the content into sections for each file
    file_sections = re.split(r'Verifying file: ', content)[1:]

    if not file_sections:
        print("No files found in the report.")
        return

    for section in file_sections:
        lines = section.strip().split('\n')
        filename = lines[0].strip()
        total_files += 1

        # Check the last line of the section for the summary
        last_line = lines[-1]
        
        if last_line.startswith('✅'):
            passed_files.append(filename)
        else:
            # This file failed, now find the failure reasons
            failed_reasons = {}
            for line in lines:
                if "failed" in line:
                    reason_match = re.search(r'failed \((.*?)\)', line)
                    if reason_match:
                        reason = reason_match.group(1)
                        failed_reasons[reason] = failed_reasons.get(reason, 0) + 1
            
            # Find the most frequent reason for failure
            if failed_reasons:
                most_frequent_reason = max(failed_reasons, key=failed_reasons.get)
            else:
                most_frequent_reason = "Unknown"

            failed_files[filename] = most_frequent_reason

    print("--- Verification Report Summary ---")
    print(f"Total files processed: {total_files}\n")
    print(f"✅ **Files that PASSED all filters:** {len(passed_files)}")
    if passed_files:
        for f in passed_files:
            print(f"- {f}")
    
    print(f"\n⚠️ **Files that FAILED one or more filters:** {len(failed_files)}")
    if failed_files:
        for f, reason in failed_files.items():
            print(f"- {f} (Most common failure reason: {reason})")

# Run the summary script on your report file
summarize_verification_report("verification_report.txt")
