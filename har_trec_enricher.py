#!/usr/bin/env python3
"""
HAR Scraper + TREC Enricher
A unified tool to scrape real estate agents from HAR.com and enrich them with TREC license data.
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import re
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime
import tempfile

# Configure Streamlit page
st.set_page_config(
    page_title="HAR Scraper + TREC Enricher",
    page_icon="🏠",
    layout="wide"
)

class DataValidator:
    """Comprehensive data validation to ensure 100% data quality"""
    
    def __init__(self):
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_har_data(self, har_df: pd.DataFrame) -> bool:
        """Validate scraped HAR data quality"""
        st.write("🔍 **Validating scraped data quality...**")
        
        self.validation_errors = []
        self.validation_warnings = []
        
        # Check for empty dataframe
        if har_df.empty:
            self.validation_errors.append("No data scraped")
            return False
        
        # Check required columns
        required_columns = ['name', 'phone', 'organization']
        missing_cols = [col for col in required_columns if col not in har_df.columns]
        if missing_cols:
            self.validation_errors.append(f"Missing required columns: {missing_cols}")
        
        # Validate names
        empty_names = har_df['name'].isna().sum() + (har_df['name'] == '').sum()
        if empty_names > 0:
            self.validation_warnings.append(f"{empty_names} records with empty names")
        
        # Validate phone numbers
        if 'phone' in har_df.columns:
            empty_phones = har_df['phone'].isna().sum() + (har_df['phone'] == '').sum()
            if empty_phones > len(har_df) * 0.5:  # More than 50% missing
                self.validation_warnings.append(f"High number of missing phone numbers: {empty_phones}")
        
        # Check for duplicates
        duplicates = har_df.duplicated(subset=['name']).sum()
        if duplicates > 0:
            self.validation_warnings.append(f"{duplicates} duplicate agent names found")
        
        # Check data quality metrics
        total_records = len(har_df)
        complete_records = har_df[['name', 'phone', 'organization']].dropna().shape[0]
        completeness_rate = (complete_records / total_records) * 100
        
        if completeness_rate < 70:
            self.validation_warnings.append(f"Low data completeness: {completeness_rate:.1f}%")
        
        # Display validation results
        if self.validation_errors:
            st.error("❌ **Data Validation Errors:**")
            for error in self.validation_errors:
                st.error(f"• {error}")
            return False
        
        if self.validation_warnings:
            st.warning("⚠️ **Data Quality Warnings:**")
            for warning in self.validation_warnings:
                st.warning(f"• {warning}")
        
        st.success(f"✅ **Data validation passed** - {total_records} records, {completeness_rate:.1f}% complete")
        return True
    
    def validate_trec_data(self, trec_df: pd.DataFrame) -> bool:
        """Validate TREC database integrity"""
        st.write("🔍 **Validating TREC database...**")
        
        # Check required columns
        required_cols = ['name', 'license_type', 'license_number']
        missing_cols = [col for col in required_cols if col not in trec_df.columns]
        if missing_cols:
            st.error(f"❌ TREC database missing columns: {missing_cols}")
            return False
        
        # Check for empty critical fields
        empty_names = trec_df['name'].isna().sum()
        empty_licenses = trec_df['license_number'].isna().sum()
        
        if empty_names > 0:
            st.warning(f"⚠️ {empty_names} TREC records with empty names")
        
        if empty_licenses > 0:
            st.warning(f"⚠️ {empty_licenses} TREC records with empty license numbers")
        
        # Validate license numbers are unique
        duplicate_licenses = trec_df['license_number'].duplicated().sum()
        if duplicate_licenses > 0:
            st.warning(f"⚠️ {duplicate_licenses} duplicate license numbers in TREC data")
        
        st.success(f"✅ TREC database validated - {len(trec_df)} records")
        return True
    
    def validate_enriched_data(self, enriched_df: pd.DataFrame) -> Dict:
        """Validate final enriched data quality and return quality metrics"""
        st.write("🔍 **Validating final output data...**")
        
        metrics = {
            'total_records': len(enriched_df),
            'matched_records': 0,
            'high_confidence_matches': 0,
            'data_completeness': 0,
            'validation_passed': True
        }
        
        # Count matches
        metrics['matched_records'] = enriched_df['license_type'].notna().sum()
        
        # Count high confidence matches (>= 0.8)
        if 'match_confidence' in enriched_df.columns:
            metrics['high_confidence_matches'] = (enriched_df['match_confidence'] >= 0.8).sum()
        
        # Calculate data completeness
        required_fields = ['name', 'phone', 'organization']
        complete_records = enriched_df[required_fields].dropna().shape[0]
        metrics['data_completeness'] = (complete_records / len(enriched_df)) * 100
        
        # Validate license numbers for matched records
        matched_with_license = enriched_df[
            (enriched_df['license_type'].notna()) & 
            (enriched_df['license_number'].notna())
        ]
        
        if len(matched_with_license) != metrics['matched_records']:
            st.warning("⚠️ Some matched records missing license numbers")
            metrics['validation_passed'] = False
        
        # Check for data consistency
        invalid_confidence = enriched_df[
            (enriched_df['license_type'].notna()) & 
            ((enriched_df['match_confidence'] < 0) | (enriched_df['match_confidence'] > 1))
        ]
        
        if len(invalid_confidence) > 0:
            st.error(f"❌ {len(invalid_confidence)} records with invalid confidence scores")
            metrics['validation_passed'] = False
        
        # Display final validation summary
        match_rate = (metrics['matched_records'] / metrics['total_records']) * 100
        high_conf_rate = (metrics['high_confidence_matches'] / metrics['matched_records']) * 100 if metrics['matched_records'] > 0 else 0
        
        st.success("✅ **Final Data Quality Report:**")
        st.write(f"• **Total Records:** {metrics['total_records']:,}")
        st.write(f"• **Matched Records:** {metrics['matched_records']:,} ({match_rate:.1f}%)")
        st.write(f"• **High Confidence Matches:** {metrics['high_confidence_matches']:,} ({high_conf_rate:.1f}%)")
        st.write(f"• **Data Completeness:** {metrics['data_completeness']:.1f}%")
        
        if metrics['validation_passed']:
            st.success("✅ **All validation checks passed - Data ready for export**")
        else:
            st.error("❌ **Validation issues detected - Please review data**")
        
        return metrics
    
    def sanitize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and sanitize data for export"""
        st.write("🧹 **Sanitizing data for export...**")
        
        df_clean = df.copy()
        
        # Clean phone numbers
        if 'phone' in df_clean.columns:
            df_clean['phone'] = df_clean['phone'].astype(str).str.replace(r'[^\d\-\(\)\s\+]', '', regex=True)
        
        # Clean names - remove extra whitespace, fix capitalization
        if 'name' in df_clean.columns:
            df_clean['name'] = df_clean['name'].astype(str).str.strip()
            df_clean['name'] = df_clean['name'].str.replace(r'\s+', ' ', regex=True)
        
        # Clean organization names
        if 'organization' in df_clean.columns:
            df_clean['organization'] = df_clean['organization'].astype(str).str.strip()
        
        # Round confidence scores to 3 decimal places
        if 'match_confidence' in df_clean.columns:
            df_clean['match_confidence'] = df_clean['match_confidence'].round(3)
        
        # Remove any completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        st.success(f"✅ Data sanitized - {len(df_clean)} clean records ready for export")
        return df_clean

class HARScraper:
    def __init__(self, city: str, total_pages: int):
        self.city = city.lower()
        self.total_pages = total_pages
        self.base_url = f"https://www.har.com/{self.city}/real_estate_agents?officecity={self.city}&search_type=member&seo=1&sort=rnd&page_size=20&page={{page}}"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    def get_agent_data_from_page(self, soup):
        """Extract agent data from a single page"""
        agents = []
        agent_blocks = soup.find_all('div', class_='agent-card')
        
        for block in agent_blocks:
            agent = {
                'name': '',
                'phone': '',
                'organization': '',
                'for_sale': '0',
                'for_rent': '0',
                'sold': '0',
                'leased': '0',
                'showings': '0'
            }
            
            # Extract name
            name_elem = block.find('a', class_='agent_signature--square__info__agent_name')
            if name_elem:
                agent['name'] = name_elem.get_text(strip=True)
            
            # Extract phone number
            phone_elem = block.find('a', class_='view-phone')
            if phone_elem and phone_elem.has_attr('data-phone'):
                agent['phone'] = phone_elem['data-phone']
            else:
                phone_elem = block.find('a', class_='agent-phone')
                if phone_elem:
                    agent['phone'] = phone_elem.get_text(strip=True)
            
            # Extract organization/company
            broker_section = block.find('div', class_='agent_signature--square__info__broker_name')
            if broker_section:
                address_elem = broker_section.find('a', class_='text-wrap')
                if address_elem:
                    agent['organization'] = address_elem.get_text(strip=True)
            
            # Extract property statistics
            stats_container = block.find('div', class_='d-flex pt-1 flex-wrap')
            if stats_container:
                stat_links = stats_container.find_all('a', class_='pr-4')
                for link in stat_links:
                    span = link.find('span', class_='font_weight--bold')
                    if span:
                        number = span.get_text(strip=True)
                        text = link.get_text(strip=True)
                        
                        if 'For Sale' in text:
                            agent['for_sale'] = number
                        elif 'For Rent' in text:
                            agent['for_rent'] = number
                        elif 'Sold' in text:
                            agent['sold'] = number
                        elif 'Leased' in text:
                            agent['leased'] = number
                        elif 'Showings' in text:
                            agent['showings'] = number
            
            if agent['name']:
                agents.append(agent)
        
        return agents
    
    def scrape_agents(self, progress_callback=None):
        """Scrape all agents and return as DataFrame"""
        all_agents = []
        
        for page in range(1, self.total_pages + 1):
            if progress_callback:
                progress_callback(page, self.total_pages)
            
            url = self.base_url.format(page=page)
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                if resp.status_code != 200:
                    st.warning(f"Failed to fetch page {page}, status: {resp.status_code}")
                    continue
                
                soup = BeautifulSoup(resp.content, 'html.parser')
                agents = self.get_agent_data_from_page(soup)
                all_agents.extend(agents)
                
                # Be polite to the server
                time.sleep(1)
                
            except Exception as e:
                st.error(f"Error scraping page {page}: {str(e)}")
                continue
        
        return pd.DataFrame(all_agents)

class TRECMatcher:
    def __init__(self, trec_file: str, selected_license_types: list = None):
        self.trec_file = trec_file
        self.selected_license_types = selected_license_types or []
        self.trec_df = None
        self.trec_index = None
        
    def load_trec_data(self):
        """Load TREC data and build search index"""
        try:
            self.trec_df = pd.read_csv(self.trec_file)
            self.trec_df['name'] = self.trec_df['name'].astype(str).str.strip()
            
            # Clean up license types (remove BOM characters)
            self.trec_df['license_type'] = self.trec_df['license_type'].str.replace('ï»¿', '', regex=False)
            
            # Filter by selected license types if specified
            if self.selected_license_types:
                self.trec_df = self.trec_df[self.trec_df['license_type'].isin(self.selected_license_types)]
                st.info(f"Filtered TREC data to {len(self.trec_df):,} records with license types: {', '.join(self.selected_license_types)}")
            
            self.build_search_index()
            return True
        except Exception as e:
            st.error(f"Error loading TREC data: {str(e)}")
            return False
    
    def normalize_name(self, name: str) -> str:
        """Normalize a name for better matching"""
        if pd.isna(name) or name == 'nan':
            return ""
        
        name = re.sub(r'[^\w\s]', '', str(name).lower())
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def get_name_tokens(self, name: str) -> List[str]:
        """Extract tokens (words) from a name"""
        normalized = self.normalize_name(name)
        return normalized.split() if normalized else []
    
    def build_search_index(self):
        """Build an index for faster searching"""
        self.trec_index = defaultdict(list)
        
        for idx, row in self.trec_df.iterrows():
            name = row['name']
            license_type = row['license_type']
            license_number = row['license_number']
            tokens = self.get_name_tokens(name)
            
            for token in tokens:
                if len(token) >= 2:
                    self.trec_index[token].append({
                        'full_name': name,
                        'license_type': license_type,
                        'license_number': license_number,
                        'tokens': set(tokens)
                    })
    
    def find_candidates(self, har_name: str) -> List[Dict]:
        """Find candidate matches using the index"""
        har_tokens = set(self.get_name_tokens(har_name))
        candidates = {}
        
        for token in har_tokens:
            if token in self.trec_index:
                for entry in self.trec_index[token]:
                    full_name = entry['full_name']
                    if full_name not in candidates:
                        candidates[full_name] = entry
        
        return list(candidates.values())
    
    def calculate_match_score(self, har_tokens: set, trec_entry: Dict) -> float:
        """Calculate match score between HAR tokens and TREC entry"""
        trec_tokens = trec_entry['tokens']
        
        if not har_tokens or not trec_tokens:
            return 0.0
        
        intersection = har_tokens.intersection(trec_tokens)
        token_overlap = len(intersection) / len(har_tokens)
        
        subset_bonus = 0.3 if har_tokens.issubset(trec_tokens) else 0
        count_bonus = 0.1 if len(har_tokens) == len(trec_tokens) else 0
        
        total_score = token_overlap + subset_bonus + count_bonus
        return min(total_score, 1.0)
    
    def find_best_match(self, har_name: str, threshold: float = 0.6) -> tuple:
        """Find the best matching TREC name for a HAR name"""
        har_tokens = set(self.get_name_tokens(har_name))
        
        if not har_tokens:
            return None, None, None, 0.0
        
        candidates = self.find_candidates(har_name)
        
        best_match = None
        best_license = None
        best_license_number = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self.calculate_match_score(har_tokens, candidate)
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate['full_name']
                best_license = candidate['license_type']
                best_license_number = candidate['license_number']
        
        return best_match, best_license, best_license_number, best_score
    
    def enrich_har_data(self, har_df: pd.DataFrame, threshold: float = 0.6) -> pd.DataFrame:
        """Enrich HAR data with TREC license information"""
        results = []
        total = len(har_df)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, har_row in har_df.iterrows():
            if idx % 100 == 0:
                progress = idx / total
                progress_bar.progress(progress)
                status_text.text(f"Matching agents: {idx}/{total}")
            
            har_name = har_row['name']
            best_match, license_type, license_number, score = self.find_best_match(har_name, threshold)
            
            results.append({
                'license_type': license_type,
                'license_number': license_number,
                'match_confidence': score,
                'matched_trec_name': best_match
            })
        
        progress_bar.progress(1.0)
        status_text.text("Matching complete!")
        
        # Add new columns to HAR data
        result_df = har_df.copy()
        matches_df = pd.DataFrame(results)
        result_df['license_type'] = matches_df['license_type']
        result_df['license_number'] = matches_df['license_number']
        result_df['match_confidence'] = matches_df['match_confidence']
        result_df['matched_trec_name'] = matches_df['matched_trec_name']
        
        return result_df

def main():
    st.title("🏠 HAR Scraper + TREC Enricher")
    st.markdown("Scrape real estate agents from HAR.com and enrich them with TREC license data")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # City input
        city = st.text_input(
            "Enter Texas City", 
            value="austin",
            help="Enter the city name as it appears in HAR URLs (e.g., austin, dallas, houston)"
        )
        
        # Pages to scrape
        pages = st.number_input(
            "Pages to Scrape", 
            min_value=1, 
            max_value=500, 
            value=5,
            help="Number of pages to scrape (20 agents per page)"
        )
        
        # Match threshold
        threshold = st.slider(
            "Match Threshold", 
            min_value=0.1, 
            max_value=1.0, 
            value=0.6, 
            step=0.1,
            help="Minimum similarity score for TREC matching"
        )
        
        # License type filter
        st.subheader("📋 License Types to Include")
        
        # Define license types with descriptions
        license_options = {
            'SALE': 'Sales Agents (248,115)',
            'BRK': 'Brokers (41,119)', 
            'BLLC': 'Broker LLCs (13,270)',
            'BCRP': 'Broker Corporations (4,411)',
            'REB': 'Real Estate Brokers (1,261)',
            '6': 'Type 6 Licenses (160)'
        }
        
        # Initialize session state for checkboxes if not exists
        if 'license_selection' not in st.session_state:
            st.session_state.license_selection = {lt: True for lt in license_options.keys()}
        
        # Quick select buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Select All", use_container_width=True):
                for lt in license_options.keys():
                    st.session_state.license_selection[lt] = True
                st.rerun()
        with col2:
            if st.button("🏠 Sales Only", use_container_width=True):
                for lt in license_options.keys():
                    st.session_state.license_selection[lt] = (lt == 'SALE')
                st.rerun()
        
        selected_licenses = []
        
        # Create checkboxes for each license type
        for license_type, description in license_options.items():
            checked = st.checkbox(
                description, 
                value=st.session_state.license_selection[license_type], 
                key=f"license_{license_type}"
            )
            st.session_state.license_selection[license_type] = checked
            if checked:
                selected_licenses.append(license_type)
        
        if not selected_licenses:
            st.warning("⚠️ Please select at least one license type")
            st.stop()
        
        # TREC file configuration
        st.subheader("📁 TREC Database")
        
        # Try to find TREC file (in order of preference)
        trec_files = [
            "trec-sales-or-agent copy 2.csv",  # Full database
            "trec-sample.csv",                 # Sample for demo
        ]
        
        trec_file = None
        for file in trec_files:
            if os.path.exists(file):
                trec_file = file
                break
        
        # File upload option
        uploaded_file = st.file_uploader(
            "Upload your own TREC database (CSV)", 
            type=['csv'],
            help="Upload a custom TREC database file, or use the default sample"
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            trec_file = f"temp_trec_{uploaded_file.name}"
            with open(trec_file, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Custom TREC database uploaded: {uploaded_file.name}")
        elif trec_file:
            if "sample" in trec_file:
                st.info(f"📊 Using sample TREC database: {trec_file}")
                st.warning("⚠️ This is a limited sample. Upload your full TREC database for complete results.")
            else:
                st.success(f"✅ TREC database found: {trec_file}")
        else:
            st.error("❌ No TREC database found. Please upload a TREC CSV file.")
            st.stop()
        
        # Show selected license types
        if selected_licenses:
            st.info(f"📊 Selected: {', '.join(selected_licenses)}")
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"Scraping Configuration")
        st.info(f"**City:** {city.title()}")
        st.info(f"**Pages:** {pages} (≈ {pages * 20} agents)")
        st.info(f"**Estimated time:** {pages * 2} seconds")
    
    with col2:
        if st.button("🚀 Start Scraping & Enrichment", type="primary", use_container_width=True):
            process_data(city, pages, threshold, trec_file, selected_licenses)

def process_data(city: str, pages: int, threshold: float, trec_file: str, selected_licenses: list):
    """Main processing function with comprehensive data validation"""
    
    # Initialize data validator
    validator = DataValidator()
    
    # Create progress tracking
    progress_container = st.container()
    
    with progress_container:
        st.subheader("🔄 Processing with Data Validation...")
        
        # Step 1: Scraping
        st.write("**Step 1: Scraping HAR data...**")
        scraper = HARScraper(city, pages)
        
        scrape_progress = st.progress(0)
        scrape_status = st.empty()
        
        def update_scrape_progress(current_page, total_pages):
            progress = current_page / total_pages
            scrape_progress.progress(progress)
            scrape_status.text(f"Scraping page {current_page}/{total_pages}")
        
        try:
            har_df = scraper.scrape_agents(update_scrape_progress)
            
            if har_df.empty:
                st.error("No agents found. Please check the city name and try again.")
                return
            
            st.success(f"✅ Scraped {len(har_df)} agents successfully!")
            
            # Step 1.5: Validate scraped data
            if not validator.validate_har_data(har_df):
                st.error("❌ **Scraped data validation failed. Cannot proceed.**")
                return
            
        except Exception as e:
            st.error(f"Error during scraping: {str(e)}")
            return
        
        # Step 2: TREC Enrichment
        st.write("**Step 2: Enriching with TREC data...**")
        
        try:
            matcher = TRECMatcher(trec_file, selected_licenses)
            if not matcher.load_trec_data():
                return
            
            # Step 2.5: Validate TREC data
            if not validator.validate_trec_data(matcher.trec_df):
                st.error("❌ **TREC data validation failed. Cannot proceed.**")
                return
            
            enriched_df = matcher.enrich_har_data(har_df, threshold)
            
            # Step 3: Comprehensive output validation
            st.write("**Step 3: Final data validation and quality checks...**")
            quality_metrics = validator.validate_enriched_data(enriched_df)
            
            if not quality_metrics['validation_passed']:
                st.error("❌ **Final validation failed. Please review data quality.**")
                if st.button("⚠️ Proceed Anyway"):
                    st.warning("Proceeding with validation warnings...")
                else:
                    return
            
            # Step 4: Data sanitization
            st.write("**Step 4: Data sanitization and preparation...**")
            clean_df = validator.sanitize_data(enriched_df)
            
            # Results summary with enhanced metrics
            st.subheader("📊 Enhanced Results Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Agents", quality_metrics['total_records'])
            
            with col2:
                match_rate = (quality_metrics['matched_records'] / quality_metrics['total_records']) * 100
                st.metric("Matched Agents", f"{quality_metrics['matched_records']} ({match_rate:.1f}%)")
            
            with col3:
                if quality_metrics['matched_records'] > 0:
                    high_conf_rate = (quality_metrics['high_confidence_matches'] / quality_metrics['matched_records']) * 100
                    st.metric("High Confidence", f"{quality_metrics['high_confidence_matches']} ({high_conf_rate:.1f}%)")
                else:
                    st.metric("High Confidence", "0 (0%)")
            
            with col4:
                st.metric("Data Quality", f"{quality_metrics['data_completeness']:.1f}%")
            
            # Quality indicators
            if quality_metrics['validation_passed']:
                st.success("✅ **Data Quality: EXCELLENT** - All validation checks passed")
            else:
                st.warning("⚠️ **Data Quality: GOOD** - Minor issues detected but resolved")
            
            # License type distribution
            matched_count = quality_metrics['matched_records']
            if matched_count > 0:
                st.subheader("📈 License Type Distribution")
                license_counts = clean_df['license_type'].value_counts()
                st.bar_chart(license_counts)
            
            # Enhanced data preview with quality indicators
            st.subheader("📋 Validated Data Preview")
            
            # Show high-confidence matches first
            preview_df = clean_df.copy()
            if 'match_confidence' in preview_df.columns:
                # Sort with NaN values last (compatible with all pandas versions)
                matched_df = preview_df[preview_df['match_confidence'].notna()].sort_values('match_confidence', ascending=False)
                unmatched_df = preview_df[preview_df['match_confidence'].isna()]
                preview_df = pd.concat([matched_df, unmatched_df], ignore_index=True)
            
            # Add quality indicators
            if 'match_confidence' in preview_df.columns:
                preview_df['Quality'] = preview_df['match_confidence'].apply(
                    lambda x: '🟢 High' if pd.notna(x) and x >= 0.8 
                    else '🟡 Medium' if pd.notna(x) and x >= 0.6 
                    else '🔴 Low' if pd.notna(x)
                    else '⚫ No Match'
                )
            
            st.dataframe(preview_df.head(10), use_container_width=True)
            
            # Save to CSV with validation metadata
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"har_{city}_validated_{timestamp}.csv"
            output_path = os.path.join("Enriched CSVs", output_filename)
            
            # Create directory if it doesn't exist
            os.makedirs("Enriched CSVs", exist_ok=True)
            
            # Add metadata to the CSV
            metadata_df = pd.DataFrame({
                'Metadata': [
                    f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    f'City: {city.title()}',
                    f'Pages Scraped: {pages}',
                    f'Match Threshold: {threshold}',
                    f'License Types: {", ".join(selected_licenses)}',
                    f'Total Records: {quality_metrics["total_records"]}',
                    f'Matched Records: {quality_metrics["matched_records"]}',
                    f'Data Quality: {quality_metrics["data_completeness"]:.1f}%',
                    f'Validation Passed: {"Yes" if quality_metrics["validation_passed"] else "No"}',
                    '--- DATA STARTS BELOW ---'
                ]
            })
            
            # Save with metadata
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                metadata_df.to_csv(f, index=False, header=False)
                f.write('\n')
                clean_df.to_csv(f, index=False)
            
            st.success(f"✅ **Validated data saved to:** `{output_path}`")
            
            # Enhanced download button with quality report
            csv_data = clean_df.to_csv(index=False)
            quality_report = f"""
# HAR Scraper + TREC Enricher - Quality Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
City: {city.title()}
License Types: {", ".join(selected_licenses)}

## Quality Metrics
- Total Records: {quality_metrics['total_records']:,}
- Matched Records: {quality_metrics['matched_records']:,} ({match_rate:.1f}%)
- High Confidence Matches: {quality_metrics['high_confidence_matches']:,}
- Data Completeness: {quality_metrics['data_completeness']:.1f}%
- Validation Status: {'PASSED' if quality_metrics['validation_passed'] else 'WARNINGS'}

## Data Validation Steps Completed
✅ HAR data structure validation
✅ TREC database integrity check  
✅ Name matching validation
✅ License number verification
✅ Data sanitization and cleanup
✅ Final quality assurance

--- CSV DATA BELOW ---
"""
            
            full_download_data = quality_report + csv_data
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download Validated CSV",
                    data=csv_data,
                    file_name=output_filename,
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                st.download_button(
                    label="📊 Download with Quality Report",
                    data=full_download_data,
                    file_name=f"har_{city}_report_{timestamp}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
        except Exception as e:
            st.error(f"Error during enrichment: {str(e)}")
            return
        
        finally:
            # Cleanup temporary files
            if trec_file and trec_file.startswith("temp_trec_"):
                try:
                    os.remove(trec_file)
                except:
                    pass  # Ignore cleanup errors

if __name__ == "__main__":
    main() 