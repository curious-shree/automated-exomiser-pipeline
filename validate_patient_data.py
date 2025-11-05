import os
import pandas as pd
import re

# --- CONFIGURATION SECTION (Must match your YML Generator script) ---

# Full path to the CSV file (FIXED: added /home/user prefix)
# NOTE: You MUST replace /home/user/ with your actual home directory path
PATIENT_DATA_FULL_PATH = "/home/user/Documents/Exomiser/exomiser-cli-14.0.0/hpoid_24_25.csv"

# -------------------------------------------------------------------

def extract_hpo_data(features_string):
    """
    Parses the 'Key Clinical Features/Symptoms' string to extract HPO IDs and descriptions.
    This function is identical to the one in the YML generator.
    Returns: (['HP:ID1', 'HP:ID2'], ['Description1', 'Description2'])
    """
    hpo_ids = []
    hpo_descriptions = []
    
    # Regex to find the pattern: Description (HP:ID)
    matches = re.findall(r'([^,]+)\s+\((HP:\d{4,})\)', features_string)
    
    for desc_with_suffix, hpo_id in matches:
        # Clean the description: remove trailing whitespace and the opening parenthesis
        clean_desc = desc_with_suffix.strip().rsplit('(', 1)[0].strip()
        hpo_ids.append(hpo_id)
        hpo_descriptions.append(clean_desc)

    return hpo_ids, hpo_descriptions

def main():
    """Reads the patient CSV file and performs data validation checks on the terminal."""
    print("=====================================================")
    print("--- Starting Patient Data Validation Check (HPO Extraction) ---")
    print("=====================================================")
    
    try:
        # Read the CSV file
        df = pd.read_csv(PATIENT_DATA_FULL_PATH)
        patient_records = df.to_dict('records')
        
        if not patient_records:
            print("❌ ERROR: The patient data file was empty or contained no records.")
            return

        print(f"Found {len(patient_records)} patient records to validate.")
        
        valid_patients_count = 0
        
        # Validation Loop
        for record in patient_records:
            # Safely get patient details
            patient_id = record.get('Patient ID (MBWE)', 'N/A')
            gender = record.get('Gender', 'N/A').upper()
            
            # Extract HPO IDs using the dedicated function
            hpo_ids, hpo_descs = extract_hpo_data(record.get('Key Clinical Features/Symptoms', ''))
            
            if hpo_ids:
                print(f"\n✅ Patient: {patient_id} | Gender: {gender}")
                print(f"   Extracted HPO IDs ({len(hpo_ids)}): {hpo_ids}")
                valid_patients_count += 1
            else:
                print(f"\n⚠️ Patient: {patient_id} | Gender: {gender} - SKIPPED")
                print("   Reason: No valid HPO IDs (HP:XXXX) found in the features column.")
        
        print(f"\n=====================================================")
        print(f"VALIDATION COMPLETE: {valid_patients_count} records passed HPO extraction.")
        print(f"=====================================================")
        
    except FileNotFoundError:
        print(f"❌ ERROR: Patient data file not found at '{PATIENT_DATA_FULL_PATH}'.")
        print("Please ensure the path in the script's CONFIGURATION SECTION is correct.")
    except Exception as e:
        print(f"❌ An error occurred during validation: {e}")

if __name__ == "__main__":
    main()
