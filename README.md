# 🎮 PS4 File Renamer

A powerful Python script to automatically rename PS4 `.pkg` files to a standardized, descriptive format using CSV and JSON data sources.
This script complements my other script, [PS4-SCRAPER](https://github.com/Axekinn/ps4-scraper). I recommend using the CSV file already generated there as an example.

## 📋 Table of Contents

- [Features](#-features)
- [Output Format](#-output-format)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [Data Sources](#-data-sources)
- [Configuration](#-configuration)
- [Safety Features](#-safety-features)
- [Examples](#-examples)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- **🔄 Batch Renaming**: Process multiple PS4 `.pkg` files simultaneously
- **📊 Multiple Data Sources**: Support for both CSV and JSON game databases
- **🛡️ Safety First**: Dry-run mode and optional backup creation
- **📝 Detailed Logging**: Comprehensive logs and reports for all operations
- **🎯 Smart Parsing**: Advanced filename parsing for various PS4 package formats
- **🧹 Filename Sanitization**: Automatic cleanup of invalid characters
- **📈 Progress Tracking**: Real-time statistics and progress reporting

## 🎯 Output Format

The script renames files to this standardized format:
```
Game Name [UPDATE Version][CUSA Identifier].pkg
```

**Example transformations:**
- `UP0017-CUSA00012_00-DCUOLPS4LIVE0001-A0283-V0100.pkg`
- → `DC Universe Online [UPDATE 2.83][CUSA00012].pkg`

## 🔧 Prerequisites

- Python 3.7 or higher
- Required Python packages:
  ```bash
  pandas
  requests
  ```

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Axekinn/ps4-renamer.git
   cd ps4-renamer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data sources:**
   - Place your CSV and/or JSON files in the same directory as the script
   - Ensure your target directory contains `.pkg` files

## 🚀 Usage

### Basic Usage

```bash
python ps4-renamer.py
```

The script will prompt you for:
- Target directory containing `.pkg` files
- Confirmation for renaming operations
- Backup preferences

### Command Line Options

```python
# Initialize with custom settings
renamer = PS4FileRenamer(
    target_directory="/path/to/pkg/files",
    log_level="DEBUG"  # DEBUG, INFO, WARNING, ERROR
)
```

### Workflow

1. **🔍 Detection**: Script automatically finds CSV/JSON files in current directory
2. **📚 Loading**: Builds game database from data sources
3. **🧪 Dry Run**: Shows what changes would be made (no actual renaming)
4. **✅ Confirmation**: User confirms before actual renaming
5. **💾 Backup** (Optional): Creates backup of original files
6. **🔄 Rename**: Performs actual file renaming
7. **📊 Report**: Generates detailed JSON report

## 📊 Data Sources

### CSV Format
Your CSV file should contain these columns:
```csv
Title_ID,Title_Name,Version,Filename,Download_URL,Size_Bytes,SHA1_Hash
CUSA00012,DC Universe Online,2.83,filename.pkg,http://...,1234567890,abc123...
```

### JSON Format
```json
{
  "results": [
    {
      "status": "found",
      "title_id": "CUSA00012",
      "title_name": "DC Universe Online",
      "latest_version": "2.83",
      "updates": {...}
    }
  ]
}
```

## ⚙️ Configuration

### Filename Patterns Supported

The script handles various PS4 package naming conventions:

1. **Standard Format**: `UP0017-CUSA00012_00-DCUOLPS4LIVE0001-A0283-V0100.pkg`
2. **Alternative Format**: `EP9000-CUSA00008_00-KZ4RELEASE000041-A0181-V0100.pkg`
3. **Simple Format**: `CUSA00012-TITLEID-V0283.pkg`

### Version Formatting

- Input: `0283` → Output: `2.83`
- Input: `0110` → Output: `1.10`
- Input: `1.50` → Output: `1.50` (already formatted)

## 🛡️ Safety Features

### Dry Run Mode
- **Always runs first** before actual renaming
- Shows exact changes that would be made
- No files are modified during dry run

### Backup System
```
💾 SECURITY BACKUP
──────────────────────────────────────────────────
🔍 What is a backup?
   • A complete copy of your folder before modifications
   • Allows you to restore original files if something goes wrong
   • Created in a separate folder (e.g., ps4-updates_backup)

✅ Advantages:
   • Maximum security - no risk of data loss
   • Ability to undo all modifications
   • Peace of mind
```

### Error Handling
- Comprehensive error logging
- Graceful handling of parsing failures
- Detailed error reports in JSON format

## 📋 Examples

### Sample Output
```
📂 Loading data sources...
📊 Found CSV files: ['ps4_games.csv']
📚 Loaded 1,247 games into database

🧪 Performing dry run...
📊 Dry Run Results:
   Total files: 15
   Would rename: 12
   Errors: 1
   Skipped: 2

✅ Dry run completed successfully!
📋 Sample renames:
   1. UP0017-CUSA00012_00-DCUOLPS4LIVE0001-A0283-V0100.pkg
      -> DC Universe Online [UPDATE 2.83][CUSA00012].pkg
```

### Generated Reports

The script creates detailed JSON reports:

```json
{
  "statistics": {
    "total_files": 15,
    "processed": 13,
    "renamed": 12,
    "errors": 1,
    "skipped": 2
  },
  "dry_run": false,
  "database_size": 1247,
  "renamed_files": [...],
  "errors": [...],
  "target_directory": "/path/to/files"
}
```

## 🐛 Troubleshooting

### Common Issues

**❌ "No CSV or JSON files found"**
- Ensure data files are in the same directory as the script
- Check file extensions (.csv, .json)

**❌ "Could not parse filename"**
- File doesn't match supported PS4 package naming patterns
- Check the log file for detailed parsing attempts

**❌ "No game info found for CUSA##### in database"**
- CUSA identifier not present in your data sources
- Verify your CSV/JSON contains the specific game

### Log Files

Check `ps4_renamer.log` for detailed operation logs:
```
2024-01-15 10:30:45 - INFO - PS4 File Renamer initialized
2024-01-15 10:30:46 - INFO - Loaded 1247 records from CSV: games.csv
2024-01-15 10:30:47 - WARNING - Could not parse filename: invalid_file.pkg
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the PS4 homebrew community for providing game databases
- Inspired by the need for organized PS4 game libraries

---

**⚠️ Disclaimer**: This tool is for educational purposes only. Ensure you have the legal right to modify and use any PS4 game files.
