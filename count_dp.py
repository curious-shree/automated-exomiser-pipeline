import vcf
import os
import sys

def count_omitted_dp_variants(file_path, dp_cutoff):
    """
    Counts total variants and variants with DP <= a specified cutoff in a single VCF file.
    Returns a tuple: (total_variants, omitted_variants)
    """
    total_variants = 0
    omitted_variants = 0
    
    try:
        with open(file_path, 'r') as vcf_in:
            vcf_reader = vcf.Reader(vcf_in)
            for record in vcf_reader:
                total_variants += 1
                try:
                    # Access the DP value from the sample data
                    if not record.samples:
                        continue # Skip records with no samples
                    
                    genotype = record.samples[0]
                    if hasattr(genotype.data, 'DP'):
                        dp = genotype.data.DP
                        # Check if DP value is valid and less than or equal to the cutoff
                        if dp is not None and int(dp) <= dp_cutoff:
                            omitted_variants += 1
                    
                except (ValueError, TypeError):
                    # In case the DP value is not a valid integer, count it as an omission
                    omitted_variants += 1
                except Exception as e:
                    sys.stderr.write(f"Error processing variant at {record.CHROM}:{record.POS} in {os.path.basename(file_path)}: {e}\n")
    
    except FileNotFoundError:
        sys.stderr.write(f"Error: The file '{file_path}' was not found.\n")
        return None
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred while processing '{file_path}': {e}\n")
        return None

    return total_variants, omitted_variants

def analyze_directory_for_dp_cutoff(input_dir, dp_cutoff=12):
    """
    Analyzes all VCF files in a directory to determine how many variants
    would be omitted by a DP cutoff.
    """
    if not os.path.exists(input_dir):
        print(f"Error: Directory not found at {input_dir}")
        return

    print("--- DP Cutoff Analysis ---\n")
    print(f"Using a DP cutoff of > {dp_cutoff} to count omitted variants.\n")
    
    for filename in os.listdir(input_dir):
        if filename.endswith(".vcf"):
            input_vcf_path = os.path.join(input_dir, filename)
            
            result = count_omitted_dp_variants(input_vcf_path, dp_cutoff)
            
            if result is not None:
                total_variants, omitted_variants = result
                percentage_omitted = (omitted_variants / total_variants) * 100 if total_variants > 0 else 0
                
                print(f"File: {filename}")
                print(f"  Total variants: {total_variants}")
                print(f"  Variants with DP <= {dp_cutoff}: {omitted_variants}")
                print(f"  Percentage omitted: {percentage_omitted:.2f}%\n")

# Define the directory and DP cutoff
input_vcf_dir = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/vcf_files"
dp_cutoff_value = 12

# Run the analysis
analyze_directory_for_dp_cutoff(input_vcf_dir, dp_cutoff_value)
