#!/usr/bin/env python3
"""
Optimized Real Estate Agent Name Matching Script

This script efficiently matches agent names between a TREC file (full legal names) 
and a HAR file (normal names) to add license type information.

Usage:
    python match_agents_optimized.py <trec_file> <har_file> [output_file]
"""

import pandas as pd
import numpy as np
import re
import sys
import os
from typing import Dict, List, Optional
import argparse
from collections import defaultdict

class OptimizedAgentNameMatcher:
    def __init__(self, trec_file: str, har_file: str):
        """Initialize the matcher with file paths."""
        self.trec_file = trec_file
        self.har_file = har_file
        self.trec_df = None
        self.har_df = None
        self.trec_index = None
        
    def load_data(self):
        """Load both CSV files."""
        print(f"Loading TREC data from {self.trec_file}...")
        self.trec_df = pd.read_csv(self.trec_file)
        print(f"Loaded {len(self.trec_df)} TREC records")
        
        print(f"Loading HAR data from {self.har_file}...")
        self.har_df = pd.read_csv(self.har_file)
        print(f"Loaded {len(self.har_df)} HAR records")
        
        # Clean up data
        self.trec_df['name'] = self.trec_df['name'].astype(str).str.strip()
        self.har_df['name'] = self.har_df['name'].astype(str).str.strip()
        
        # Create search index
        print("Building search index...")
        self.build_search_index()
        
    def normalize_name(self, name: str) -> str:
        """Normalize a name for better matching."""
        if pd.isna(name) or name == 'nan':
            return ""
        
        # Convert to lowercase, remove extra spaces, remove punctuation
        name = re.sub(r'[^\w\s]', '', str(name).lower())
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def get_name_tokens(self, name: str) -> List[str]:
        """Extract tokens (words) from a name."""
        normalized = self.normalize_name(name)
        return normalized.split() if normalized else []
    
    def build_search_index(self):
        """Build an index for faster searching."""
        self.trec_index = defaultdict(list)
        
        for idx, row in self.trec_df.iterrows():
            name = row['name']
            license_type = row['license_type']
            tokens = self.get_name_tokens(name)
            
            # Index by individual tokens and token pairs
            for token in tokens:
                if len(token) >= 2:  # Only index meaningful tokens
                    self.trec_index[token].append({
                        'full_name': name,
                        'license_type': license_type,
                        'tokens': set(tokens)
                    })
    
    def find_candidates(self, har_name: str) -> List[Dict]:
        """Find candidate matches using the index."""
        har_tokens = set(self.get_name_tokens(har_name))
        candidates = {}
        
        # Find all TREC entries that share at least one token
        for token in har_tokens:
            if token in self.trec_index:
                for entry in self.trec_index[token]:
                    full_name = entry['full_name']
                    if full_name not in candidates:
                        candidates[full_name] = entry
        
        return list(candidates.values())
    
    def calculate_match_score(self, har_tokens: set, trec_entry: Dict) -> float:
        """Calculate match score between HAR tokens and TREC entry."""
        trec_tokens = trec_entry['tokens']
        
        if not har_tokens or not trec_tokens:
            return 0.0
        
        # Token overlap ratio (main scoring method)
        intersection = har_tokens.intersection(trec_tokens)
        token_overlap = len(intersection) / len(har_tokens)
        
        # Bonus if HAR name is completely contained in TREC name
        subset_bonus = 0.3 if har_tokens.issubset(trec_tokens) else 0
        
        # Bonus for exact token count match (same number of name parts)
        count_bonus = 0.1 if len(har_tokens) == len(trec_tokens) else 0
        
        total_score = token_overlap + subset_bonus + count_bonus
        return min(total_score, 1.0)
    
    def find_best_match(self, har_name: str, threshold: float = 0.6) -> tuple:
        """Find the best matching TREC name for a HAR name."""
        har_tokens = set(self.get_name_tokens(har_name))
        
        if not har_tokens:
            return None, None, 0.0
        
        candidates = self.find_candidates(har_name)
        
        best_match = None
        best_license = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self.calculate_match_score(har_tokens, candidate)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate['full_name']
                best_license = candidate['license_type']
        
        return best_match, best_license, best_score
    
    def match_all_agents(self, threshold: float = 0.6) -> pd.DataFrame:
        """Match all HAR agents to TREC agents."""
        results = []
        total = len(self.har_df)
        
        print(f"Matching {total} HAR agents...")
        
        for idx, har_row in self.har_df.iterrows():
            if idx % 1000 == 0:
                progress = (idx / total) * 100
                print(f"Progress: {progress:.1f}% ({idx}/{total})")
                
            har_name = har_row['name']
            best_match, license_type, score = self.find_best_match(har_name, threshold)
            
            results.append({
                'har_name': har_name,
                'matched_trec_name': best_match,
                'license_type': license_type,
                'match_confidence': score
            })
        
        print("Matching complete!")
        return pd.DataFrame(results)
    
    def add_license_column(self, output_file: str = None, threshold: float = 0.6):
        """Add license type column to HAR data and save result."""
        # Perform matching
        matches_df = self.match_all_agents(threshold)
        
        # Add new columns to original HAR data
        result_df = self.har_df.copy()
        result_df['license_type'] = matches_df['license_type']
        result_df['match_confidence'] = matches_df['match_confidence']
        result_df['matched_trec_name'] = matches_df['matched_trec_name']
        
        # Generate output filename if not provided
        if output_file is None:
            base_name = os.path.splitext(os.path.basename(self.har_file))[0]
            output_file = f"{base_name}_with_licenses.csv"
        
        # Save result
        result_df.to_csv(output_file, index=False)
        
        # Print statistics
        matched_count = result_df['license_type'].notna().sum()
        total_count = len(result_df)
        match_rate = (matched_count / total_count) * 100
        
        print(f"\n=== RESULTS ===")
        print(f"Total HAR agents: {total_count:,}")
        print(f"Successfully matched: {matched_count:,}")
        print(f"Match rate: {match_rate:.1f}%")
        print(f"Output saved to: {output_file}")
        
        # Show license type distribution
        license_counts = result_df['license_type'].value_counts()
        print(f"\nLicense type distribution:")
        for license_type, count in license_counts.items():
            print(f"  {license_type}: {count:,}")
        
        # Show some examples of high-confidence matches
        print(f"\nSample high-confidence matches:")
        high_conf_matches = result_df[
            (result_df['license_type'].notna()) & 
            (result_df['match_confidence'] >= 0.8)
        ].head(10)
        
        for _, row in high_conf_matches.iterrows():
            print(f"  '{row['name']}' -> '{row['matched_trec_name']}' "
                  f"({row['license_type']}, confidence: {row['match_confidence']:.2f})")
        
        # Show some examples of unmatched agents
        unmatched = result_df[result_df['license_type'].isna()].head(5)
        if len(unmatched) > 0:
            print(f"\nSample unmatched agents (consider lowering threshold):")
            for _, row in unmatched.iterrows():
                print(f"  '{row['name']}'")
        
        return result_df

def main():
    parser = argparse.ArgumentParser(description='Match real estate agent names between TREC and HAR files')
    parser.add_argument('trec_file', help='Path to TREC CSV file')
    parser.add_argument('har_file', help='Path to HAR CSV file')
    parser.add_argument('-o', '--output', help='Output file path (optional)')
    parser.add_argument('-t', '--threshold', type=float, default=0.6, 
                       help='Minimum similarity threshold for matching (default: 0.6)')
    
    args = parser.parse_args()
    
    # Check if files exist
    if not os.path.exists(args.trec_file):
        print(f"Error: TREC file '{args.trec_file}' not found")
        sys.exit(1)
    
    if not os.path.exists(args.har_file):
        print(f"Error: HAR file '{args.har_file}' not found")
        sys.exit(1)
    
    # Create matcher and run
    matcher = OptimizedAgentNameMatcher(args.trec_file, args.har_file)
    matcher.load_data()
    result_df = matcher.add_license_column(args.output, args.threshold)
    
    print(f"\n✅ Matching complete! Your HAR file now has license type information.")
    print(f"   You can reuse this script with future HAR files that have the same format.")

if __name__ == "__main__":
    main() 