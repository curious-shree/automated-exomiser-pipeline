import vcf
import os
import sys

def filter_vcf_variant(variant):
    """
    Applies quality, genotype quality (GQ), depth (DP), and
    Variant Allele Frequency (VAF) filters to a VCF variant record.
    Returns True if the variant passes the filters, False otherwise.
    """
    try:
        # 1. Quality Filters (QUAL > 30)
        # Using a default value to handle None
        qual = variant.QUAL if variant.QUAL is not None else 0
        if qual < 30:
            return False

        # Check if the variant has any samples before proceeding
        if not variant.samples:
            return False
        
        genotype = variant.samples[0]
        
        # Check if genotype data exists
        if not hasattr(genotype, 'data'):
            return False

        # 2. Genotype Quality (GQ) Filter (GQ > 20)
        # Safely access GQ using .get() to avoid KeyError
        gq = getattr(genotype.data, 'GQ', None)
        if gq is None or int(gq) < 20:
            return False

        # 3. Depth (DP) Filter (DP > 12)
        # Safely access DP using .get()
        dp = getattr(genotype.data, 'DP', None)
        if dp is None or int(dp) < 12:
            return False

        # 4. Variant Allele Frequency (VAF) Filter (VAF > 0.45)
        ad = getattr(genotype.data, 'AD', None)
        if ad and len(ad) > 1:
            try:
                ref_reads = int(ad[0])
                alt_reads = int(ad[1])
                total_reads = ref_reads + alt_reads
                if total_reads > 0:
                    vaf = alt_reads / total_reads
                    if vaf < 0.45:
                        return False
            except (ValueError, IndexError, TypeError):
                # Handle cases where AD values are not convertible to int or list is too short
                return False
        else:
            # If AD field is missing or malformed, we can't calculate VAF, so filter it out.
            return False

    except Exception as e:
        # A more specific error message for debugging
        sys.stderr.write(f"Error processing variant {variant.CHROM}:{variant.POS} in filter_vcf_variant: {e}\n")
        return False

    return True

def filter_vcf_directory(input_dir, output_dir):
    """
    Reads all VCF files from a directory, applies filters, and
    writes the filtered variants to a new directory.
    """
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            sys.stderr.write(f"Error creating directory {output_dir}: {e}\n")
            return # Exit if directory cannot be created

    for filename in os.listdir(input_dir):
        if filename.endswith(".vcf"):
            input_vcf_path = os.path.join(input_dir, filename)
            # Create a clean output filename
            base_filename = os.path.splitext(filename)[0]
            output_filename = f"{base_filename}_filtered.vcf"
            output_vcf_path = os.path.join(output_dir, output_filename)
            
            try:
                # Open VCF file for reading
                with open(input_vcf_path, 'r') as vcf_in:
                    vcf_reader = vcf.Reader(vcf_in)
                    
                    # Open output file for writing
                    with open(output_vcf_path, 'w') as vcf_out:
                        vcf_writer = vcf.Writer(vcf_out, vcf_reader)

                        # Track if any records were written to avoid creating empty files
                        records_written = 0

                        for record in vcf_reader:
                            if filter_vcf_variant(record):
                                vcf_writer.write_record(record)
                                records_written += 1
                                # The original print statement is here, modified for clarity and robustness
                                try:
                                    vaf = float(record.samples[0].data.AD[1]) / sum(map(int, record.samples[0].data.AD))
                                    dp = record.samples[0].data.DP
                                    print(f"Variant: {record.CHROM}:{record.POS} | VAF: {vaf:.2f} | DP: {dp}")
                                except (ValueError, TypeError, AttributeError):
                                    print(f"Variant: {record.CHROM}:{record.POS} passed filters, but display failed.")

                if records_written == 0:
                    print(f"No variants passed filters in '{filename}'. Empty output file '{output_filename}' created.")
                else:
                    print(f"Successfully filtered '{filename}'. Filtered variants saved to '{output_vcf_path}'")

            except FileNotFoundError:
                sys.stderr.write(f"Error: The file '{input_vcf_path}' was not found.\n")
            except vcf.parser.ParseError as pe:
                sys.stderr.write(f"Skipping '{filename}' due to a parsing error: {pe}\n")
            except Exception as e:
                sys.stderr.write(f"An unexpected error occurred while processing '{filename}': {e}\n")

# Define the input and output directories
input_vcf_dir = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/vcf_files"
output_vcf_dir = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/filtered_vcf_dir" # Corrected to be a directory

# Run the filtering process
filter_vcf_directory(input_vcf_dir, output_vcf_dir)
