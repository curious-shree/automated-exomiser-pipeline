import vcf
import os
import numpy as np

def analyze_vcf_metrics(input_dir):
    """
    Analyzes key metrics (QUAL, DP, GQ, VAF) across all VCF files in a directory
    and provides statistical summaries.
    """
    all_quals = []
    all_dps = []
    all_gqs = []
    all_vafs = []
    
    # Iterate through all files in the input directory
    for filename in os.listdir(input_dir):
        if not filename.endswith(".vcf"):
            continue
        
        file_path = os.path.join(input_dir, filename)
        print(f"Analyzing metrics in: {filename}")
        
        try:
            with open(file_path, 'r') as f:
                vcf_reader = vcf.Reader(f)
                
                for record in vcf_reader:
                    # Collect QUAL values
                    if record.QUAL is not None:
                        all_quals.append(float(record.QUAL))
                    
                    if not record.samples:
                        continue
                    
                    sample = record.samples[0]
                    
                    # Collect DP (Depth) values
                    if hasattr(sample.data, 'DP') and sample.data.DP is not None:
                        all_dps.append(int(sample.data.DP))
                    
                    # Collect GQ (Genotype Quality) values
                    if hasattr(sample.data, 'GQ') and sample.data.GQ is not None:
                        all_gqs.append(int(sample.data.GQ))
                    
                    # Collect VAF (Variant Allele Frequency) values from AD field
                    if hasattr(sample.data, 'AD') and sample.data.AD and len(sample.data.AD) > 1:
                        ref_reads, alt_reads = int(sample.data.AD[0]), int(sample.data.AD[1])
                        total_reads = ref_reads + alt_reads
                        if total_reads > 0:
                            all_vafs.append(alt_reads / total_reads)
        
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Generate and print a statistical summary for each metric
    print("\n--- Statistical Summary ---")
    
    def print_stats(metric_name, data):
        if not data:
            print(f"No data collected for {metric_name}.")
            return
        
        print(f"\n{metric_name} Statistics (across all files):")
        print(f"  Min: {np.min(data):.2f}")
        print(f"  25th Percentile: {np.percentile(data, 25):.2f}")
        print(f"  Median (50th Percentile): {np.median(data):.2f}")
        print(f"  75th Percentile: {np.percentile(data, 75):.2f}")
        print(f"  Max: {np.max(data):.2f}")
    
    print_stats("Quality (QUAL)", all_quals)
    print_stats("Depth (DP)", all_dps)
    print_stats("Genotype Quality (GQ)", all_gqs)
    print_stats("Variant Allele Frequency (VAF)", all_vafs)
    

# Define the path to your raw input VCF files
input_vcf_dir = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/vcf_files"

# Run the analysis
analyze_vcf_metrics(input_vcf_dir)
