# Real Estate Agent Name Matching Tool

This tool matches agent names between TREC files (full legal names) and HAR files (normal names) to add license type information to HAR data.

## Files

- `match_agents_optimized.py` - The main optimized matching script (recommended)
- `match_agents.py` - Basic version (slower, for reference)

## Usage

### Basic Usage
```bash
python3 match_agents_optimized.py "trec-sales-or-agent copy.csv" "your_har_file.csv"
```

### Advanced Usage
```bash
python3 match_agents_optimized.py "trec-sales-or-agent copy.csv" "your_har_file.csv" -o "output_filename.csv" -t 0.6
```

### Parameters
- `trec_file` - Path to the TREC CSV file (contains full legal names and license types)
- `har_file` - Path to the HAR CSV file (contains agent names to be matched)
- `-o, --output` - Optional: Custom output filename (default: `har_filename_with_licenses.csv`)
- `-t, --threshold` - Optional: Matching confidence threshold (default: 0.6, range: 0.0-1.0)

## Input File Requirements

### TREC File Format
Must contain these columns:
- `license_number` - License number
- `name` - Full legal name
- `license_type` - License type (SALE, BRK, etc.)

### HAR File Format
Must contain at least:
- `name` - Agent name to be matched

Other columns will be preserved in the output.

## Output

The script creates a new CSV file with:
- All original HAR columns preserved
- `license_type` - License type from TREC file
- `match_confidence` - Confidence score (0.0-1.0)
- `matched_trec_name` - Full legal name that was matched

## Results Summary

For the current Dallas HAR file:
- **Total agents**: 11,127
- **Successfully matched**: 11,062 (99.4%)
- **License types found**:
  - SALE: 9,753 agents
  - BRK: 1,253 agents  
  - BLLC: 36 agents
  - REB: 14 agents
  - BCRP: 6 agents

## Matching Algorithm

The tool uses an optimized fuzzy matching algorithm that:

1. **Tokenizes names** - Splits names into individual words
2. **Creates search index** - Builds a fast lookup index from TREC names
3. **Finds candidates** - Quickly identifies potential matches
4. **Scores matches** - Uses multiple criteria:
   - Token overlap ratio (main factor)
   - Subset matching (HAR name contained in TREC name)
   - Token count similarity

## Examples of Successful Matches

- `John Beasly` → `John Michael Beasly` (SALE)
- `Elizabeth Conroy` → `Kathryn Elizabeth Conroy` (SALE)
- `Mia Vincent` → `MIA RAE VINCENT` (SALE)

## Adjusting Match Threshold

- **Higher threshold (0.8-1.0)**: More conservative, fewer but higher-confidence matches
- **Lower threshold (0.4-0.6)**: More liberal, more matches but some may be incorrect
- **Default (0.6)**: Good balance for most use cases

## Installation Requirements

```bash
pip3 install pandas numpy
```

## Future Use

This script is designed to be reusable with any future HAR files that have the same format. Simply run:

```bash
python3 match_agents_optimized.py "trec-sales-or-agent copy.csv" "new_har_file.csv"
```

The TREC file remains unchanged and can be reused for all future matching operations. 