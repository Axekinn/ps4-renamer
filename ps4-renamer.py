#!/usr/bin/env python3
"""
PS4 Game File Renamer Script
Renames PS4 .pkg files based on CSV and JSON data sources
Format: "Game Name [UPDATE Version][CUSA Identifier].pkg"
"""

import os
import re
import csv
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import requests

class PS4FileRenamer:
    def __init__(self, target_directory: str, log_level: str = 'INFO'):
        """
        Initialize the PS4 File Renamer
        
        Args:
            target_directory: Directory containing .pkg files to rename
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.target_directory = Path(target_directory)
        self.game_database = {}
        self.renamed_files = []
        self.errors = []
        
        # Setup logging
        self.setup_logging(log_level)
        
        # Validate target directory
        if not self.target_directory.exists():
            raise ValueError(f"Target directory does not exist: {target_directory}")
    
    def setup_logging(self, log_level: str):
        """Setup logging configuration"""
        log_file = Path("ps4_renamer.log")
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("PS4 File Renamer initialized")
    
    def load_csv_data(self, csv_file: str) -> int:
        """
        Load game data from CSV file
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            Number of records loaded
        """
        try:
            df = pd.read_csv(csv_file)
            loaded_count = 0
            
            # Check for required columns
            required_columns = ['Title_ID', 'Title_Name', 'Version']
            
            # Handle different CSV formats based on your files
            if 'Title_ID' in df.columns and 'Title_Name' in df.columns:
                for _, row in df.iterrows():
                    title_id = str(row['Title_ID']).strip()
                    title_name = str(row['Title_Name']).strip()
                    
                    # Extract CUSA from Title_ID if present
                    cusa_match = re.search(r'(CUSA\d+)', title_id)
                    if cusa_match:
                        cusa = cusa_match.group(1)
                        
                        # Get version if available
                        version = str(row.get('Version', '1.00')).strip()
                        
                        self.game_database[cusa] = {
                            'name': title_name,
                            'version': version,
                            'source': f'CSV:{csv_file}'
                        }
                        loaded_count += 1
            
            self.logger.info(f"Loaded {loaded_count} records from CSV: {csv_file}")
            return loaded_count
            
        except Exception as e:
            self.logger.error(f"Error loading CSV {csv_file}: {e}")
            return 0
    
    def load_json_data(self, json_file: str) -> int:
        """
        Load game data from JSON file
        
        Args:
            json_file: Path to JSON file
            
        Returns:
            Number of records loaded
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            loaded_count = 0
            
            # Handle different JSON structures
            if 'results' in data:
                # Handle the sample JSON format from your files
                for result in data['results']:
                    if result.get('status') == 'found' and 'updates' in result:
                        title_id = result.get('title_id', '')
                        title_name = result.get('title_name', result.get('sony_game_name', ''))
                        
                        cusa_match = re.search(r'(CUSA\d+)', title_id)
                        if cusa_match and title_name:
                            cusa = cusa_match.group(1)
                            
                            # Get latest version from updates
                            latest_version = result.get('latest_version', '1.00')
                            
                            self.game_database[cusa] = {
                                'name': title_name,
                                'version': latest_version,
                                'source': f'JSON:{json_file}'
                            }
                            loaded_count += 1
            
            self.logger.info(f"Loaded {loaded_count} records from JSON: {json_file}")
            return loaded_count
            
        except Exception as e:
            self.logger.error(f"Error loading JSON {json_file}: {e}")
            return 0
    
    def parse_filename(self, filename: str) -> Optional[Dict[str, str]]:
        """
        Parse PS4 .pkg filename to extract components
        
        Args:
            filename: Original filename
            
        Returns:
            Dictionary with parsed components or None if parsing fails
        """
        # Remove .pkg extension
        base_name = filename.replace('.pkg', '')
        
        # Pattern for PS4 .pkg files: UP####-CUSA#####_##-TITLEID-A####-V####
        patterns = [
            # Standard format: UP0017-CUSA00012_00-DCUOLPS4LIVE0001-A0283-V0100_5.pkg
            r'([A-Z]{2}\d+)-([A-Z]{4}\d+)_\d+-([A-Z0-9]+)-A(\d+)-V(\d+)(?:_(\d+))?',
            # Alternative format: EP9000-CUSA00008_00-KZ4RELEASE000041-A0181-V0100.pkg
            r'([A-Z]{2}\d+)-([A-Z]{4}\d+)_\d+-([A-Z0-9]+)-A(\d+)-V(\d+)',
            # Simple format: CUSA00012-TITLEID-V0283.pkg
            r'([A-Z]{4}\d+)-([A-Z0-9]+)-V(\d+)',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, base_name)
            if match:
                groups = match.groups()
                
                if len(groups) >= 5:  # Full format
                    return {
                        'publisher': groups[0],
                        'cusa': groups[1],
                        'title_code': groups[2],
                        'app_version': groups[3],
                        'version': groups[4],
                        'part': groups[5] if len(groups) > 5 and groups[5] else None
                    }
                elif len(groups) >= 3:  # Simple format
                    return {
                        'cusa': groups[0],
                        'title_code': groups[1],
                        'version': groups[2],
                        'publisher': None,
                        'app_version': None,
                        'part': None
                    }
        
        self.logger.warning(f"Could not parse filename: {filename}")
        return None
    
    def format_version(self, version_str: str) -> str:
        """
        Format version string for display
        
        Args:
            version_str: Raw version string
            
        Returns:
            Formatted version string
        """
        if not version_str:
            return "1.00"
        
        # If version is already in the correct format (e.g., "01.10"), return as is
        if re.match(r'^\d{1,2}\.\d{2}$', version_str):
            return version_str
        
        # Otherwise, treat as a version number from filename (e.g., "0110" -> "1.10")
        try:
            # Handle formats like "0283" -> "2.83"
            if len(version_str) >= 3:
                major = str(int(version_str[:-2])) if version_str[:-2] else "1"
                minor = version_str[-2:]
                return f"{major}.{minor}"
            else:
                return f"1.{version_str.zfill(2)}"
        except:
            return version_str
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        
        # Trim and return
        return filename.strip()
    
    def generate_new_filename(self, parsed_data: Dict[str, str], original_filename: str) -> Optional[str]:
        """
        Generate new filename based on parsed data and database lookup
        
        Args:
            parsed_data: Parsed filename components
            original_filename: Original filename
            
        Returns:
            New filename or None if generation fails
        """
        cusa = parsed_data.get('cusa')
        if not cusa:
            return None
        
        # Look up game info in database
        game_info = self.game_database.get(cusa)
        if not game_info:
            self.logger.warning(f"No game info found for {cusa} in database")
            return None
        
        game_name = game_info['name']
        
        # CORRECTION: Always use the version from the CSV database
        # instead of the version from the filename
        version = game_info.get('version', '1.00')
        formatted_version = self.format_version(version)
        
        # Handle multi-part files
        part_suffix = ""
        if parsed_data.get('part'):
            part_suffix = f"_Part{parsed_data['part']}"
        
        # Generate new filename
        new_filename = f"{game_name} [UPDATE {formatted_version}][{cusa}]{part_suffix}.pkg"
        
        # Sanitize the filename
        new_filename = self.sanitize_filename(new_filename)
        
        return new_filename
    
    def rename_file(self, old_path: Path, new_filename: str, dry_run: bool = False) -> bool:
        """
        Rename a single file
        
        Args:
            old_path: Current file path
            new_filename: New filename
            dry_run: If True, don't actually rename files
            
        Returns:
            True if successful, False otherwise
        """
        new_path = old_path.parent / new_filename
        
        # Check if target file already exists
        if new_path.exists():
            self.logger.warning(f"Target file already exists: {new_filename}")
            return False
        
        try:
            if not dry_run:
                old_path.rename(new_path)
                self.logger.info(f"Renamed: {old_path.name} -> {new_filename}")
            else:
                self.logger.info(f"[DRY RUN] Would rename: {old_path.name} -> {new_filename}")
            
            self.renamed_files.append({
                'original': str(old_path.name),
                'new': new_filename,
                'path': str(old_path.parent)
            })
            return True
            
        except Exception as e:
            self.logger.error(f"Error renaming {old_path.name}: {e}")
            self.errors.append({
                'file': str(old_path.name),
                'error': str(e)
            })
            return False
    
    def process_directory(self, dry_run: bool = True) -> Dict[str, int]:
        """
        Process all .pkg files in the target directory
        
        Args:
            dry_run: If True, don't actually rename files
            
        Returns:
            Statistics about the processing
        """
        pkg_files = list(self.target_directory.glob("*.pkg"))
        self.logger.info(f"Found {len(pkg_files)} .pkg files to process")
        
        stats = {
            'total_files': len(pkg_files),
            'processed': 0,
            'renamed': 0,
            'errors': 0,
            'skipped': 0
        }
        
        for pkg_file in pkg_files:
            try:                
                # Parse the filename
                parsed_data = self.parse_filename(pkg_file.name)
                if not parsed_data:
                    self.logger.warning(f"Could not parse filename: {pkg_file.name}")
                    stats['errors'] += 1
                    continue
                
                # Generate new filename
                new_filename = self.generate_new_filename(parsed_data, pkg_file.name)
                if not new_filename:
                    self.logger.warning(f"Could not generate new filename for: {pkg_file.name}")
                    stats['errors'] += 1
                    continue
                
                # Rename the file
                if self.rename_file(pkg_file, new_filename, dry_run):
                    stats['renamed'] += 1
                else:
                    stats['errors'] += 1
                
                stats['processed'] += 1
                
            except Exception as e:
                self.logger.error(f"Error processing {pkg_file.name}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def create_backup(self) -> str:
        """
        Create a backup of the target directory
        
        Returns:
            Path to backup directory
        """
        backup_dir = self.target_directory.parent / f"{self.target_directory.name}_backup"
        
        try:
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            shutil.copytree(self.target_directory, backup_dir)
            self.logger.info(f"Backup created: {backup_dir}")
            return str(backup_dir)
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise
    
    def save_report(self, stats: Dict[str, int], dry_run: bool = True):
        """
        Save a detailed report of the renaming process
        
        Args:
            stats: Processing statistics
            dry_run: Whether this was a dry run
        """
        report_file = Path(f"ps4_rename_report_{'dryrun' if dry_run else 'actual'}.json")
        
        report = {
            'statistics': stats,
            'dry_run': dry_run,
            'database_size': len(self.game_database),
            'renamed_files': self.renamed_files,
            'errors': self.errors,
            'target_directory': str(self.target_directory)
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Report saved: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving report: {e}")

def load_csv_data(csv_file):
    """Load CSV data and organize by Title_ID"""
    games_data = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title_id = row['Title_ID']
            if title_id not in games_data:
                games_data[title_id] = {
                    'title_name': row['Title_Name'],
                    'version': row['Version'],  # Use version directly from CSV
                    'download_links': []
                }
            
            games_data[title_id]['download_links'].append({
                'filename': row['Filename'],
                'url': row['Download_URL'],
                'size': int(row['Size_Bytes']) if row['Size_Bytes'] else 0,
                'sha1': row['SHA1_Hash']
            })
    
    return games_data

def create_updates_structure(games_data):
    """Create updates structure using CSV data"""
    updates = {}
    
    for title_id, game_info in games_data.items():
        # Use version directly from CSV
        version = game_info['version']
        
        updates[title_id] = {
            "name": game_info['title_name'],
            "versions": {
                version: {
                    "files": game_info['download_links']
                }
            }
        }
    
    return updates

def ask_for_backup() -> bool:
    """
    Ask the user if they want to create a backup
    
    Returns:
        True if user wants to create a backup, False otherwise
    """
    print("\n💾 SECURITY BACKUP")
    print("─" * 50)
    print("🔍 What is a backup?")
    print("   • A complete copy of your folder before modifications")
    print("   • Allows you to restore original files if something goes wrong")
    print("   • Created in a separate folder (e.g., ps4-updates_backup)")
    print()
    print("✅ Advantages:")
    print("   • Maximum security - no risk of data loss")
    print("   • Ability to undo all modifications")
    print("   • Peace of mind")
    print()
    print("❌ Disadvantages:")
    print("   • Uses double disk space temporarily")
    print("   • Creation time depends on file sizes")
    print()
    
    while True:
        choice = input("🤔 Create a backup before renaming? (y/N): ").strip().lower()
        if choice in ['y', 'yes']:
            return True
        elif choice in ['n', 'no', '']:
            return False
        else:
            print("❓ Please answer with 'y' (yes) or 'n' (no)")

def main():
    """Main function to run the PS4 File Renamer"""
    
    # Configuration - UPDATE THESE PATHS
    TARGET_DIRECTORY = input("Enter the directory containing .pkg files: ").strip()
    
    if not TARGET_DIRECTORY:
        print("❌ No directory specified. Exiting.")
        return
    
    # Initialize the renamer
    try:
        renamer = PS4FileRenamer(TARGET_DIRECTORY)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    # Load data sources
    print("📂 Loading data sources...")
    
    # Look for CSV and JSON files in current directory
    csv_files = list(Path('.').glob('*.csv'))
    json_files = list(Path('.').glob('*.json'))
    
    if csv_files:
        print(f"📊 Found CSV files: {[f.name for f in csv_files]}")
        for csv_file in csv_files:
            renamer.load_csv_data(str(csv_file))
    
    if json_files:
        print(f"📋 Found JSON files: {[f.name for f in json_files]}")
        for json_file in json_files:
            renamer.load_json_data(str(json_file))
    
    if not csv_files and not json_files:
        print("❌ No CSV or JSON files found in current directory!")
        return
    
    print(f"📚 Loaded {len(renamer.game_database)} games into database")
    
    # Dry run first
    print("\n🧪 Performing dry run...")
    dry_run_stats = renamer.process_directory(dry_run=True)
    
    print(f"\n📊 Dry Run Results:")
    print(f"   Total files: {dry_run_stats['total_files']}")
    print(f"   Would rename: {dry_run_stats['renamed']}")
    print(f"   Errors: {dry_run_stats['errors']}")
    print(f"   Skipped: {dry_run_stats['skipped']}")
    
    # Save dry run report
    renamer.save_report(dry_run_stats, dry_run=True)
    
    if dry_run_stats['renamed'] > 0:
        print(f"\n✅ Dry run completed successfully!")
        print(f"📋 Sample renames:")
        for i, rename in enumerate(renamer.renamed_files[:3]):
            print(f"   {i+1}. {rename['original']}")
            print(f"      -> {rename['new']}")
        
        # Ask for confirmation
        confirm = input(f"\n❓ Proceed with actual renaming of {dry_run_stats['renamed']} files? (y/N): ").strip().lower()
        
        if confirm == 'y':
            # Ask if user wants backup
            create_backup = ask_for_backup()
            
            backup_path = None
            if create_backup:
                print("\n💾 Creating backup...")
                try:
                    backup_path = renamer.create_backup()
                    print(f"✅ Backup created: {backup_path}")
                except Exception as e:
                    print(f"❌ Could not create backup: {e}")
                    retry = input("🔄 Continue without backup? (y/N): ").strip().lower()
                    if retry != 'y':
                        print("❌ Operation cancelled.")
                        return
            else:
                print("⚠️  Proceeding without backup...")
            
            # Reset for actual run
            renamer.renamed_files = []
            renamer.errors = []
            
            # Perform actual renaming
            print("\n🔄 Performing actual renaming...")
            actual_stats = renamer.process_directory(dry_run=False)
            
            print(f"\n🎉 Actual Renaming Results:")
            print(f"   Total files: {actual_stats['total_files']}")
            print(f"   Successfully renamed: {actual_stats['renamed']}")
            print(f"   Errors: {actual_stats['errors']}")
            print(f"   Skipped: {actual_stats['skipped']}")
            
            # Save actual report
            renamer.save_report(actual_stats, dry_run=False)
            
            print(f"\n✅ Renaming process completed!")
            print(f"📋 Check ps4_rename_report_actual.json for detailed results")
            
            if backup_path:
                print(f"💾 Backup available at: {backup_path}")
                print("   To restore: delete current files and copy backup files back")
            
        else:
            print("❌ Renaming cancelled by user.")
    
    else:
        print("❌ No files would be renamed. Check your data sources and file formats.")
    
    csv_file = "ps4_titles_download_links.csv"
    output_file = "ps4_titles_with_updates_corrected.json"
    
    print("Loading CSV data...")
    games_data = load_csv_data(csv_file)
    
    print(f"Found {len(games_data)} unique games")
    
    print("Creating updates structure...")
    updates = create_updates_structure(games_data)
    
    # Create final structure
    final_structure = {
        "updates": updates,
        "metadata": {
            "total_games": len(updates),
            "generated_from": "ps4_titles_download_links.csv",
            "note": "Versions extracted directly from CSV Version column"
        }
    }
    
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_structure, f, indent=2, ensure_ascii=False)
    
    print("Done!")
    
    # Display some examples for verification
    print("\nExamples of detected versions:")
    examples = ['CUSA00006', 'CUSA00016', 'CUSA00013', 'CUSA00003', 'CUSA00012']
    for title_id in examples:
        if title_id in updates:
            game = updates[title_id]
            version = list(game['versions'].keys())[0]
            print(f"- {game['name']} ({title_id}): version {version}")

if __name__ == "__main__":
    main()