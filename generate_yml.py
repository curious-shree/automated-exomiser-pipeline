import os
import yaml
import copy # Import the copy module

def create_exomiser_yml(vcf_path, hpo_id, output_dir, age, gender):
    """
    Creates five Exomiser YAML files with different pathogenicity sources.
    """
    scoring_systems = {
        'pms': ['POLYPHEN', 'MUTATIONTASTER'],
        'rm': ['REVEL', 'MVP'],
        'cd': ['CADD'],
        'rem': ['REMM'],
        'si': ['SPLICEAI']
    }

    # Extract base file name from the VCF path
    base_name = os.path.splitext(os.path.basename(vcf_path))[0]

    # Static YAML configuration
    base_config = {
        'analysis': {
            'genomeAssembly': 'hg38',
            'vcf': vcf_path,
            'hpoIds': [hpo_id],
            'analysisMode': 'SINGLETON',
            'frequencySources': [
                'GNOMAD_EXOMES',
                'GNOMAD_GENOMES'
            ]
        },
        'outputOptions': {
            'outputDirectory': output_dir,
            'outputPrefix': base_name,
            'outputFormats': ['HTML', 'TSV']
        }
    }

    # Generate a YAML file for each scoring system
    for suffix, sources in scoring_systems.items():
        # Make a deep copy to prevent modifying the base dictionary in complex scenarios
        config = copy.deepcopy(base_config)
        config['analysis']['pathogenicitySources'] = sources

        output_filename = f"{base_name}.{suffix}.yml"
        output_path = os.path.join(output_dir, output_filename)

        try:
            with open(output_path, 'w') as f:
                yaml.dump(config, f, sort_keys=False)
            print(f"✅ Created {output_filename}")
        except Exception as e:
            print(f"❌ Error creating {output_filename}: {e}")

def main():
    """
    Main function to handle user input and generate YAML files.
    """
    print("--- Exomiser YAML File Generator ---")

    try:
        num_patients = int(input("How many patients are you processing? "))
    except ValueError:
        print("❗ Invalid number. Exiting.")
        return

    for i in range(num_patients):
        print(f"\n--- Patient {i+1} of {num_patients} ---")

        try:
            vcf_path = input("Enter the filtered VCF file path: ")
            hpo_id = input("Enter the HPO ID (e.g., HP:0001250): ")
            output_dir = input("Enter the output directory to save the .yml files: ")
            age = int(input("Enter patient's age (in years): "))
            gender = input("Enter patient's gender (MALE/FEMALE/UNKNOWN): ").upper()

            # Create the output directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Created output directory: {output_dir}")

            create_exomiser_yml(vcf_path, hpo_id, output_dir, age, gender)

        except ValueError:
            print("❗ Invalid input for age. Please enter a whole number.")
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue

if __name__ == "__main__":
    main()
