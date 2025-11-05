import vcf
import os
import sys

def passes_filters(record):
    """
    Re-checks all filter criteria for a VCF record.
    Returns True if the record passes, False otherwise, along with a reason.
    """
    try:
        # 1. QUAL filter (QUAL > 30)
        qual = float(record.QUAL) if record.QUAL is not None else -1
        if qual < 30:
            return False, "QUAL"

        if not record.samples:
            return False, "NoSample"
        
        sample = record.samples[0]
        
        # 2. GQ filter (GQ > 20)
        if hasattr(sample.data, 'GQ'):
            gq = sample.data.GQ
            if gq is None or int(gq) < 20:
                return False, "GQ"
        else:
            return False, "NoGQ"
            
        # 3. DP filter (DP > 12)
        if hasattr(sample.data, 'DP'):
            dp = sample.data.DP
            if dp is None or int(dp) < 12:
                return False, "DP"
        else:
            return False, "NoDP"
            
        # 4. VAF filter (VAF > 0.45)
        if hasattr(sample.data, 'AD'):
            ad = sample.data.AD
            if ad and len(ad) > 1:
                try:
                    ref_reads = int(ad[0])
                    alt_reads = int(ad[1])
                    total_reads = ref_reads + alt_reads
                    if total_reads > 0:
                        vaf = alt_reads / total_reads
                        if vaf < 0.45:
                            return False, "VAF"
                    else:
                        return False, "ZeroReads"
                except (ValueError, IndexError):
                    return False, "AD_Format_Error"
            else:
                return False, "AD_Missing"
        else:
            return False, "NoAD"
            
    except Exception as e:
        return False, f"Error: {e}"

    return True, "Passed"

def verify_filtered_vcf(filtered_dir):
    """
    Checks all VCFs in a directory and reports on the terminal.
    """
    passed_files = []
    failed_files = []

    if not os.path.exists(filtered_dir):
        print(f"Error: Directory not found at {filtered_dir}")
        return

    print("Starting VCF file verification...\n")
    
    for filename in os.listdir(filtered_dir):
        if filename.endswith(".vcf"):
            file_path = os.path.join(filtered_dir, filename)
            
            total_variants = 0
            failed_variants = 0

            try:
                with open(file_path, "r") as f:
                    vcf_reader = vcf.Reader(f)
                    
                    for record in vcf_reader:
                        total_variants += 1
                        passes, reason = passes_filters(record)
                        if not passes:
                            failed_variants += 1
                            sys.stderr.write(f"  - Variant {record.CHROM}:{record.POS} in '{filename}' failed due to: {reason}\n")
                            
            except vcf.parser.ParseError as pe:
                print(f"  - Skipped '{filename}' due to a parsing error: {pe}")
                failed_files.append(f"{filename} (Parse Error)")
                continue
            except Exception as e:
                print(f"  - An unexpected error occurred with '{filename}': {e}")
                failed_files.append(f"{filename} (Unexpected Error)")
                continue

            if failed_variants > 0:
                print(f"\nVerification failed for '{filename}': {failed_variants} out of {total_variants} variants failed the filters.")
                failed_files.append(filename)
            else:
                print(f"\nVerification passed for '{filename}': All {total_variants} variants passed the filters.")
                passed_files.append(filename)

    print("\n" + "="*50)
    print("Verification Summary")
    print("="*50)
    
    if passed_files:
        print("\n✅ **Files that passed verification:**")
        for f in passed_files:
            print(f" - {f}")
    else:
        print("\n❌ **No files passed the verification.**")

    if failed_files:
        print("\n❌ **Files that failed verification:**")
        for f in failed_files:
            print(f" - {f}")
    else:
        print("\n✅ **All files passed the verification.**")
    
    print("="*50)

# Define the directory to verify
filtered_vcf_dir = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/filtered_vcf_dir"

# Run the verification
verify_filtered_vcf(filtered_vcf_dir)
