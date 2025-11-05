import subprocess
from pathlib import Path
import os
import sys
import argparse
from datetime import datetime
from typing import List, Tuple

# --- CONFIGURATION ---

# Dynamically set the home directory. This fixes case-sensitivity issues 
# like /Home vs /home and removes the need for a hardcoded username.
HOME_DIR = Path.home() 

# 1. Base directory where the exomiser-cli-14.0.0.jar file is located
# Assuming the structure: /home/<username>/Documents/Exomiser/exomiser-cli-14.0.0
# If your Exomiser directory name uses an UNDERSCORE instead of a HYPHEN (exomiser_cli_14.0.0), 
# you MUST change the last component below.
EXOMISER_BASE_DIR = HOME_DIR / "Documents" / "Exomiser" / "exomiser-cli-14.0.0"

# 2. Directory containing all the patient folders
YML_ROOT_DIR = EXOMISER_BASE_DIR / "yml_files"

# 3. Path to the executable JAR file
EXOMISER_JAR = EXOMISER_BASE_DIR / "exomiser-cli-14.0.0.jar"

# 4. Java memory setting (adjust based on your machine's available RAM)
JAVA_MEMORY_FLAG = "-Xmx8g"

# --- MAIN EXECUTION LOGIC ---

def run_exomiser_analysis(yml_file_path: Path, verbose: bool = False) -> bool:
    """
    Executes the Exomiser CLI command for a single YAML file.
    
    Args:
        yml_file_path: Path to the YAML configuration file
        verbose: Whether to print detailed output
    
    Returns:
        bool: True if successful, False otherwise
    """
    # NOTE: Added --debug flag to the command list to force Exomiser to print
    # the exact reason for the UnsatisfiedDependencyException (usually a missing file).
    command = [
        "java",
        JAVA_MEMORY_FLAG,
        "-jar",
        str(EXOMISER_JAR),
        "--analysis",
        str(yml_file_path),
        "--debug" # <--- ADDED DEBUG FLAG HERE
    ]
    
    patient_name = yml_file_path.parent.name
    print(f"\n{'='*70}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Running: {yml_file_path.name}")
    print(f"Patient: {patient_name}")
    print(f"{'='*70}")
    
    if verbose:
        print(f"Command: {' '.join(command)}")

    try:
        # NOTE: We use cwd=str(EXOMISER_BASE_DIR) to ensure that Exomiser outputs results
        # relative to its installation directory, which is standard practice.
        result = subprocess.run(
            command, 
            check=True, 
            text=True, 
            capture_output=True,
            cwd=str(EXOMISER_BASE_DIR) 
        )
        
        print(f"✓ SUCCESS - Analysis completed for {patient_name}")
        
        if verbose and result.stdout:
            print(f"\nOutput:\n{result.stdout.strip()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ FAILED - Analysis failed for {patient_name}")
        print(f"Return Code: {e.returncode}")
        # Capture and print more of the error output since we expect the debug logs here
        error_snippet = e.stderr.strip()[:2000] + ("\n[...] FULL STACK TRACE OMITTED FOR BREVITY" if len(e.stderr.strip()) > 2000 else "")
        print(f"Error Output (Snippet, including debug):\n{error_snippet}")
        return False
        
    except FileNotFoundError:
        print("✗ ERROR - Java not found in PATH")
        print("Install Java and ensure it's accessible from command line")
        sys.exit(1)
        
    except Exception as e:
        print(f"✗ UNEXPECTED ERROR - {type(e).__name__}: {e}")
        return False


def find_yml_files(root_dir: Path) -> List[Path]:
    """
    Recursively finds all YAML files in patient subdirectories.
    
    Args:
        root_dir: Root directory to search
    
    Returns:
        List of Path objects for found YAML files, sorted alphabetically
    """
    yml_files = []
    
    # Use glob with * to find only files one level deep (the patient folders)
    all_files = list(root_dir.glob("*/*.yml")) + list(root_dir.glob("*/*.yaml"))
    
    # Filter to only include files in actual patient subdirectories (i.e., not directly in YML_ROOT_DIR)
    for file_path in all_files:
        if file_path.parent != root_dir:
            yml_files.append(file_path)

    return sorted(yml_files)


def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validates the environment setup before running analyses.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check Java installation
    try:
        result = subprocess.run(
            ["java", "-version"], 
            capture_output=True, 
            text=True,
            timeout=5 # Add timeout for safety
        )
        if result.returncode != 0 and "version" not in result.stderr.lower():
            errors.append("Java command runs but failed to return version (check installation)")
    except FileNotFoundError:
        errors.append("Java not found in PATH (ensure 'java' command is available)")
    except subprocess.TimeoutExpired:
        errors.append("Java version check timed out.")
    
    # Check JAR file
    if not EXOMISER_JAR.exists():
        errors.append(f"Exomiser JAR not found: {EXOMISER_JAR}")
    
    # Check YAML directory
    if not YML_ROOT_DIR.is_dir():
        errors.append(f"YAML root directory not found: {YML_ROOT_DIR}")
    
    return (len(errors) == 0, errors)


def main():
    """Main function to traverse directories and initiate runs."""
    
    parser = argparse.ArgumentParser(
        description="Batch runner for Exomiser variant analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (prints full command and Exomiser stdout)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be processed without running analysis"
    )
    
    args = parser.parse_args()
    
    # Environment Validation
    print(f"Starting Exomiser Batch Runner v1.2. Base Path: {EXOMISER_BASE_DIR}")
    print("Validating environment...")
    is_valid, errors = validate_environment()
    
    if not is_valid:
        print("\n✗ Environment validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print("✓ Environment validation passed\n")
    
    # Find YAML files
    print(f"Scanning for YAML files in: {YML_ROOT_DIR}")
    yml_files = find_yml_files(YML_ROOT_DIR)
    
    if not yml_files:
        print("No YAML files found in patient subdirectories. Exiting.")
        return
    
    print(f"\nFound {len(yml_files)} analysis file(s) across patient folders, ready for processing:")
    for i, yml_file in enumerate(yml_files, 1):
        print(f"  {i}. {yml_file.parent.name}/{yml_file.name}")
    
    if args.dry_run:
        print("\n[DRY RUN] Analysis commands were listed but NOT executed.")
        return
    
    # Confirmation before running large batch
    print("\n" + "="*70)
    try:
        input("Press Enter to START the batch analysis (or Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\nBatch execution cancelled by user.")
        return

    print("="*70)
    print("STARTING BATCH ANALYSIS (with --debug flag)")
    print("="*70)
    
    start_time = datetime.now()
    successful = 0
    failed = 0
    
    # Run analyses  - args.verbose
    for yml_file in yml_files:
        if run_exomiser_analysis(yml_file, verbose=True): 
            successful += 1
        else:
            failed += 1
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "="*70)
    print("BATCH RUN COMPLETE")
    print("="*70)
    print(f"Total analyses: {len(yml_files)}")
    print(f"✓ Successful: {successful}")
    print(f"✗ Failed: {failed}")
    print(f"Duration: {duration}")
    print(f"\nResults location: Check Exomiser output directories")
    print(f"  (Results are written relative to the Exomiser CLI base directory: {EXOMISER_BASE_DIR})")


if __name__ == "__main__":
    main()
