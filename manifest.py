import os
import pandas as pd
import csv
import re

# --- CONFIGURATION SECTION ---

# VCF_BASE_DIRECTORY, YML_BASE_DIRECTORY, and PATIENT_DATA_FULL_PATH have been updated 
# to use the correct Linux absolute path structure starting with a forward slash.

# Base directory where VCF files are located.
# NOTE: You MUST replace /home/user/ with your actual home directory path (e.g., /home/yourusername/) 
# OR use the shortcut ~/
VCF_BASE_DIRECTORY = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/filtered_vcf_dir"
# Base directory where the 5 generated .yml files will be saved.
YML_BASE_DIRECTORY = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/yml_files"

# File name as seen in the error output
PATIENT_DATA_FILE = "hpoid_24_25.csv" 
# Full path to the CSV file (FIXED: added /home/user prefix)
PATIENT_DATA_FULL_PATH = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/hpoid_24_25.csv"

# The script will process the FIRST patient found in the CSV file. 
# ------------------------------

# This is the template for your .yml file, based on the structure you provided.
YML_TEMPLATE = """---
analysis:
    # Exomiser version 14.0.0 is typically configured for hg38
    genomeAssembly: hg38
    # The full path to the patient's VCF file
    vcf: {vcf_full_path}
    # Pedigree file is not used in this single-sample analysis
    ped: 
    proband:
        sex: {sex}
        # List of HPO IDs for phenotypic analysis
        hpoIds: {hpo_ids_formatted_list} # {hpo_comment}
    # Default inheritance mode cut-offs
    inheritanceModes: {{
      AUTOSOMAL_DOMINANT: 0.1,
      AUTOSOMAL_RECESSIVE_HOM_ALT: 0.1,
      AUTOSOMAL_RECESSIVE_COMP_HET: 2.0,
      X_DOMINANT: 0.1,
      X_RECESSIVE_HOM_ALT: 0.1,
      X_RECESSIVE_COMP_HET: 2.0,
      MITOCHONDRIAL: 0.2
    }}
    # Use variants that passed VCF filtering
    analysisMode: PASS_ONLY
    # Population frequency sources to use
    frequencySources: [
        UK10K, THOUSAND_GENOMES, TOPMED,
        GNOMAD_E_AFR, GNOMAD_E_AMR, GNOMAD_E_EAS, GNOMAD_E_NFE, GNOMAD_E_SAS,
        GNOMAD_G_AFR, GNOMAD_G_AMR, GNOMAD_G_EAS, GNOMAD_G_NFE, GNOMAD_G_SAS
    ]
    # This section changes for each of the 5 generated files
    pathogenicitySources: {pathogenicity_sources} 
    steps: [
        failedVariantFilter: {{ }},
        variantEffectFilter: {{
          remove: [
              FIVE_PRIME_UTR_EXON_VARIANT, THREE_PRIME_UTR_EXON_VARIANT,
              FIVE_PRIME_UTR_INTRON_VARIANT, THREE_PRIME_UTR_INTRON_VARIANT,
              NON_CODING_TRANSCRIPT_EXON_VARIANT, NON_CODING_TRANSCRIPT_INTRON_VARIANT,
              CODING_TRANSCRIPT_INTRON_VARIANT, UPSTREAM_GENE_VARIANT,
              DOWNSTREAM_GENE_VARIANT, INTERGENIC_VARIANT, REGULATORY_REGION_VARIANT
            ]
        }},
        # Filter for common variants (MAF < 2.0%)
        frequencyFilter: {{maxFrequency: 2.0}},
        # Keep all variants for pathogenicity analysis (no pre-filtering by score)
        pathogenicityFilter: {{keepNonPathogenic: true}},
        # Required to evaluate inheritance modes
        inheritanceFilter: {{}},
        # Use the default HiPhive prioritizer for gene-level scoring
        omimPrioritiser: {{}},
        hiPhivePrioritiser: {{}}
    ]
outputOptions:
    outputContributingVariantsOnly: false
    numGenes: 0
    # Output file name includes the Patient ID and the scoring system suffix
    outputFileName: {output_filename}
    # Output all common formats
    outputFormats: [HTML, JSON, TSV_GENE, TSV_VARIANT, VCF]
"""

def extract_hpo_data(features_string):
    """
    Parses the 'Key Clinical Features/Symptoms' string to extract HPO IDs and descriptions.
    Returns: (['HP:ID1', 'HP:ID2'], ['Description1', 'Description2'])
    """
    hpo_ids = []
    hpo_descriptions = []
    
    # Regex to find the pattern: Description (HP:ID)
    # This handles the case where there are descriptions and HPO IDs in parentheses.
    matches = re.findall(r'([^,]+)\s+\((HP:\d+)\)', features_string)
    
    for desc_with_suffix, hpo_id in matches:
        # Clean the description: remove trailing whitespace and the opening parenthesis
        clean_desc = desc_with_suffix.strip().rsplit('(', 1)[0].strip()
        hpo_ids.append(hpo_id)
        hpo_descriptions.append(clean_desc)

    return hpo_ids, hpo_descriptions

def generate_yml_files(patient_data):
    """Generates 5 .yml files for a single patient using different scoring systems."""
    
    # Define the 5 scoring groups as requested by the user.
    scoring_systems = {
        'PSM': ['POLYPHEN', 'SIFT', 'MUTATION_TASTER'],
        'RM': ['REVEL', 'MVP'],
        'CADD': ['CADD'],
        'REMM': ['REMM'],
        'SPLICEAI': ['SPLICE_AI']
    }

    # --- Prepare HPO Data ---
    # Assuming 'Key Clinical Features/Symptoms' is the correct column name for HPO data
    hpo_ids, hpo_descs = extract_hpo_data(patient_data.get('Key Clinical Features/Symptoms', ''))
    
    if not hpo_ids:
        print(f"❌ WARNING: No valid HPO IDs found for patient {patient_data.get('Patient ID (MBWE)', 'Unknown')}. Skipping YML generation.")
        return

    # Format HPO IDs for the YML file (no quotes around individual IDs, as YAML expects)
    hpo_ids_formatted_list = str(hpo_ids).replace("'", "")
    
    # Create the comment string for clarity in the YML file
    hpo_comment_parts = [f"'{id}': {desc}" for id, desc in zip(hpo_ids, hpo_descs)]
    hpo_comment = ", ".join(hpo_comment_parts)
    
    # --- Prepare VCF and Output Paths ---
    patient_id = patient_data.get('Patient ID (MBWE)')
    if not patient_id:
        print("❌ ERROR: Could not find 'Patient ID (MBWE)' column. Cannot proceed.")
        return
    
    # Assuming VCF file name matches the Patient ID with a standard extension
    vcf_filename = f"{patient_id}.vcf.gz" 
    vcf_full_path = os.path.join(VCF_BASE_DIRECTORY, vcf_filename)
    
    # Ensure the output directory exists
    patient_yml_dir = os.path.join(YML_BASE_DIRECTORY, patient_id)
    os.makedirs(patient_yml_dir, exist_ok=True)
    
    print(f"Processing patient {patient_id} for VCF: {vcf_filename}...")

    # --- Generate the 5 YML Files ---
    for suffix, sources in scoring_systems.items():
        # Output file name pattern: PatientID_SCORE_SYSTEM.yml
        output_filename_base = f"{patient_id}_{suffix}"
        
        yml_content = YML_TEMPLATE.format(
            vcf_full_path=vcf_full_path,
            # Ensure gender is uppercase (MALE/FEMALE)
            sex=patient_data.get('Gender', 'UNKNOWN').upper(), 
            hpo_ids_formatted_list=hpo_ids_formatted_list,
            hpo_comment=hpo_comment,
            # Format the list of sources for YAML: [SOURCE1, SOURCE2]
            pathogenicity_sources=str(sources).replace("'", ""), 
            output_filename=output_filename_base
        )
        
        yml_file_path = os.path.join(patient_yml_dir, f"{output_filename_base}.yml")
        with open(yml_file_path, 'w') as f:
            f.write(yml_content)
        print(f"  ✅ Created {os.path.basename(yml_file_path)}")

def main():
    """Main function to read CSV data and generate YML files for the target patient."""
    print("--- Starting Exomiser YML Generation (Batch Mode) ---")
    
    # 1. Read the CSV file containing patient HPO data
    try:
        # Use the explicit full path to avoid relative path issues.
        df = pd.read_csv(PATIENT_DATA_FULL_PATH)
        
        # Convert dataframe to a list of dictionaries for easier processing
        patient_records = df.to_dict('records')
        
        if patient_records:
            print(f"Found {len(patient_records)} patient records to process.")
            # 2. Process ALL patients found in the CSV.
            for i, target_record in enumerate(patient_records):
                print(f"\n--- Starting Patient {i+1}/{len(patient_records)} ---")
                generate_yml_files(target_record)
            
        else:
            print("❌ ERROR: The patient data file was empty or contained no records.")
            
    except FileNotFoundError:
        print(f"❌ ERROR: Patient data file not found at '{PATIENT_DATA_FULL_PATH}'. Please ensure the path is correct.")
    except Exception as e:
        print(f"❌ An error occurred during file processing: {e}")
        
    print("\n--- YML Generation Complete ---")

if __name__ == "__main__":
    main()
