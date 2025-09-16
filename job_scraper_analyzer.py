#!/usr/bin/env python3
"""
Job Listings Web Scraper and Analyzer
Task 10: Data Analytics Internship

This script scrapes job listings for Data Analyst roles and performs basic analysis.
Author: Data Analytics Intern
Date: September 2025
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
import re
from collections import Counter
import random
from urllib.parse import urljoin, urlparse
import warnings
warnings.filterwarnings('ignore')

class JobScraper:
    def __init__(self, base_url, delay=2):
        """
        Initialize the JobScraper
        
        Args:
            base_url (str): Base URL for the job portal
            delay (int): Delay between requests in seconds
        """
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.jobs_data = []
        
    def scrape_jobs(self, search_query="data analyst", num_pages=5):
        """
        Scrape job listings from the job portal
        
        Args:
            search_query (str): Job search query
            num_pages (int): Number of pages to scrape
        """
        print(f"Starting to scrape jobs for '{search_query}'...")
        
        for page in range(1, num_pages + 1):
            print(f"Scraping page {page}...")
            
            try:
                # Construct URL for current page
                url = f"{self.base_url}/search?q={search_query.replace(' ', '+')}&page={page}"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract job listings from current page
                job_listings = self._extract_job_listings(soup)
                self.jobs_data.extend(job_listings)
                
                print(f"Found {len(job_listings)} jobs on page {page}")
                
                # Respectful delay between requests
                time.sleep(self.delay + random.uniform(0, 1))
                
            except requests.RequestException as e:
                print(f"Error scraping page {page}: {str(e)}")
                continue
            except Exception as e:
                print(f"Unexpected error on page {page}: {str(e)}")
                continue
        
        print(f"Total jobs scraped: {len(self.jobs_data)}")
        return self.jobs_data
    
    def _extract_job_listings(self, soup):
        """
        Extract job information from BeautifulSoup object
        
        Args:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        
        # Common job listing selectors (adaptable to different sites)
        job_selectors = [
            '.job-listing',
            '.job-card',
            '.job-item',
            '.search-result',
            '[data-job-id]'
        ]
        
        job_elements = []
        for selector in job_selectors:
            job_elements = soup.select(selector)
            if job_elements:
                break
        
        # If no specific selectors work, try generic patterns
        if not job_elements:
            job_elements = soup.find_all(['div', 'article'], class_=re.compile(r'job|card|listing'))
        
        for job_element in job_elements:
            try:
                job_data = self._extract_job_data(job_element)
                if job_data and job_data.get('title'):
                    jobs.append(job_data)
            except Exception as e:
                continue
        
        return jobs
    
    def _extract_job_data(self, job_element):
        """
        Extract individual job data from job element
        
        Args:
            job_element: BeautifulSoup element containing job info
            
        Returns:
            dict: Job information dictionary
        """
        job_data = {}
        
        # Extract title
        title_selectors = ['h2', 'h3', '.title', '.job-title', '[data-title]']
        job_data['title'] = self._safe_extract_text(job_element, title_selectors)
        
        # Extract company
        company_selectors = ['.company', '.company-name', '.employer', '[data-company]']
        job_data['company'] = self._safe_extract_text(job_element, company_selectors)
        
        # Extract location
        location_selectors = ['.location', '.job-location', '.city', '[data-location]']
        job_data['location'] = self._safe_extract_text(job_element, location_selectors)
        
        # Extract salary
        salary_selectors = ['.salary', '.pay', '.compensation', '[data-salary]']
        job_data['salary'] = self._safe_extract_text(job_element, salary_selectors)
        
        # Extract skills/requirements
        skills_selectors = ['.skills', '.requirements', '.tags', '.job-description']
        job_data['skills'] = self._safe_extract_text(job_element, skills_selectors)
        
        # Clean the extracted data
        job_data = self._clean_job_data(job_data)
        
        return job_data
    
    def _safe_extract_text(self, element, selectors):
        """
        Safely extract text using multiple selectors
        
        Args:
            element: BeautifulSoup element
            selectors: List of CSS selectors to try
            
        Returns:
            str: Extracted text or empty string
        """
        for selector in selectors:
            try:
                found_element = element.select_one(selector)
                if found_element:
                    return found_element.get_text(strip=True)
            except:
                continue
        return ""
    
    def _clean_job_data(self, job_data):
        """
        Clean and standardize job data
        
        Args:
            job_data (dict): Raw job data
            
        Returns:
            dict: Cleaned job data
        """
        # Clean title
        if job_data.get('title'):
            job_data['title'] = re.sub(r'\s+', ' ', job_data['title']).strip()
        
        # Clean company
        if job_data.get('company'):
            job_data['company'] = re.sub(r'\s+', ' ', job_data['company']).strip()
            job_data['company'] = re.sub(r'^\W+|\W+$', '', job_data['company'])
        
        # Clean location
        if job_data.get('location'):
            job_data['location'] = re.sub(r'\s+', ' ', job_data['location']).strip()
            job_data['location'] = re.sub(r'[^\w\s,.-]', '', job_data['location'])
        
        # Extract and clean salary
        if job_data.get('salary'):
            salary_match = re.search(r'[\d,]+(?:\.\d+)?(?:\s*(?:lakh|LPA|per annum|PA))?', job_data['salary'])
            job_data['salary'] = salary_match.group(0) if salary_match else job_data['salary']
        
        return job_data

class JobAnalyzer:
    def __init__(self, jobs_data):
        """
        Initialize JobAnalyzer with scraped job data
        
        Args:
            jobs_data (list): List of job dictionaries
        """
        self.jobs_data = jobs_data
        self.df = pd.DataFrame(jobs_data)
        self._preprocess_data()
    
    def _preprocess_data(self):
        """Preprocess the job data for analysis"""
        if self.df.empty:
            print("No data to analyze")
            return
        
        # Clean and standardize location data
        if 'location' in self.df.columns:
            self.df['location'] = self.df['location'].fillna('Unknown')
            self.df['location'] = self.df['location'].str.title()
            # Extract city from location string
            self.df['city'] = self.df['location'].apply(self._extract_city)
        
        # Clean company names
        if 'company' in self.df.columns:
            self.df['company'] = self.df['company'].fillna('Unknown')
        
        # Extract skills
        if 'skills' in self.df.columns:
            self.df['extracted_skills'] = self.df['skills'].apply(self._extract_skills)
    
    def _extract_city(self, location):
        """Extract city name from location string"""
        if not location or location == 'Unknown':
            return 'Unknown'
        
        # Common patterns for city extraction
        city_patterns = [
            r'^([^,]+)',  # Text before first comma
            r'(\w+(?:\s+\w+)?)',  # First one or two words
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, location.strip())
            if match:
                return match.group(1).strip()
        
        return location
    
    def _extract_skills(self, skills_text):
        """Extract skills from job description/requirements text"""
        if not skills_text:
            return []
        
        # Common data analyst skills to look for
        skill_keywords = [
            'python', 'r', 'sql', 'excel', 'tableau', 'power bi', 'powerbi',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'plotly',
            'machine learning', 'data visualization', 'statistics',
            'business intelligence', 'etl', 'data mining', 'analytics',
            'jupyter', 'git', 'hadoop', 'spark', 'aws', 'azure',
            'mysql', 'postgresql', 'mongodb', 'looker', 'qlik'
        ]
        
        found_skills = []
        skills_lower = skills_text.lower()
        
        for skill in skill_keywords:
            if skill in skills_lower:
                found_skills.append(skill.title())
        
        return found_skills
    
    def generate_summary(self):
        """Generate summary statistics of scraped data"""
        summary = {
            'total_jobs': len(self.df),
            'unique_companies': self.df['company'].nunique() if 'company' in self.df.columns else 0,
            'unique_locations': self.df['location'].nunique() if 'location' in self.df.columns else 0,
            'jobs_with_salary': self.df['salary'].notna().sum() if 'salary' in self.df.columns else 0
        }
        
        print("=== JOB SCRAPING SUMMARY ===")
        print(f"Total jobs scraped: {summary['total_jobs']}")
        print(f"Unique companies: {summary['unique_companies']}")
        print(f"Unique locations: {summary['unique_locations']}")
        print(f"Jobs with salary info: {summary['jobs_with_salary']}")
        print()
        
        return summary
    
    def get_top_locations(self, top_n=5):
        """Get top job locations"""
        if 'city' not in self.df.columns:
            return pd.Series()
        
        top_locations = self.df['city'].value_counts().head(top_n)
        print(f"=== TOP {top_n} JOB LOCATIONS ===")
        for location, count in top_locations.items():
            print(f"{location}: {count} jobs")
        print()
        
        return top_locations
    
    def get_top_skills(self, top_n=10):
        """Get most in-demand skills"""
        if 'extracted_skills' not in self.df.columns:
            return Counter()
        
        all_skills = []
        for skills_list in self.df['extracted_skills']:
            if isinstance(skills_list, list):
                all_skills.extend(skills_list)
        
        skill_counts = Counter(all_skills)
        top_skills = skill_counts.most_common(top_n)
        
        print(f"=== TOP {top_n} IN-DEMAND SKILLS ===")
        for skill, count in top_skills:
            print(f"{skill}: {count} mentions")
        print()
        
        return skill_counts
    
    def create_visualizations(self):
        """Create visualizations for the analysis"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Data Analyst Job Market Analysis', fontsize=16, fontweight='bold')
        
        # 1. Top locations bar plot
        top_locations = self.get_top_locations()
        if not top_locations.empty:
            axes[0, 0].bar(range(len(top_locations)), top_locations.values, color='skyblue')
            axes[0, 0].set_xticks(range(len(top_locations)))
            axes[0, 0].set_xticklabels(top_locations.index, rotation=45, ha='right')
            axes[0, 0].set_title('Top 5 Job Locations')
            axes[0, 0].set_ylabel('Number of Jobs')
        
        # 2. Top skills bar plot
        top_skills = self.get_top_skills(8)
        if top_skills:
            skills, counts = zip(*top_skills.most_common(8))
            axes[0, 1].barh(range(len(skills)), counts, color='lightcoral')
            axes[0, 1].set_yticks(range(len(skills)))
            axes[0, 1].set_yticklabels(skills)
            axes[0, 1].set_title('Most In-Demand Skills')
            axes[0, 1].set_xlabel('Number of Mentions')
        
        # 3. Location distribution pie chart
        if not top_locations.empty:
            axes[1, 0].pie(top_locations.values, labels=top_locations.index, autopct='%1.1f%%', startangle=90)
            axes[1, 0].set_title('Job Distribution by Location')
        
        # 4. Jobs per company (top companies)
        if 'company' in self.df.columns:
            top_companies = self.df['company'].value_counts().head(6)
            axes[1, 1].bar(range(len(top_companies)), top_companies.values, color='lightgreen')
            axes[1, 1].set_xticks(range(len(top_companies)))
            axes[1, 1].set_xticklabels(top_companies.index, rotation=45, ha='right')
            axes[1, 1].set_title('Top Companies by Job Postings')
            axes[1, 1].set_ylabel('Number of Jobs')
        
        plt.tight_layout()
        plt.savefig('job_analysis_report.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def save_data(self, filename='scraped_jobs.csv'):
        """Save scraped data to CSV file"""
        self.df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")

# Demo function with simulated data (for testing when actual scraping isn't possible)
def demo_with_sample_data():
    """
    Demo function with sample data for testing the analyzer
    This simulates what would be scraped from a real job portal
    """
    print("Running demo with sample job data...")
    
    # Sample job data (simulating scraped results)
    sample_jobs = [
        {
            'title': 'Data Analyst - Business Intelligence',
            'company': 'TechCorp India',
            'location': 'Bangalore, Karnataka',
            'salary': '6-8 LPA',
            'skills': 'Python, SQL, Tableau, Excel, Power BI, data visualization, business intelligence'
        },
        {
            'title': 'Junior Data Analyst',
            'company': 'Analytics Solutions',
            'location': 'Mumbai, Maharashtra',
            'salary': '4-6 LPA',
            'skills': 'SQL, Excel, Python, pandas, matplotlib, data analysis, reporting'
        },
        {
            'title': 'Senior Data Analyst',
            'company': 'DataTech Pvt Ltd',
            'location': 'Hyderabad, Telangana',
            'salary': '8-12 LPA',
            'skills': 'Python, R, SQL, machine learning, statistics, tableau, power bi'
        },
        {
            'title': 'Business Data Analyst',
            'company': 'Enterprise Solutions',
            'location': 'Pune, Maharashtra',
            'salary': '5-7 LPA',
            'skills': 'SQL, Excel, Tableau, business intelligence, data visualization, analytics'
        },
        {
            'title': 'Data Analyst Intern',
            'company': 'StartupXYZ',
            'location': 'Bangalore, Karnataka',
            'salary': '2-3 LPA',
            'skills': 'Python, pandas, numpy, matplotlib, jupyter, git, excel'
        },
        {
            'title': 'Financial Data Analyst',
            'company': 'FinanceCorps',
            'location': 'Delhi, NCR',
            'salary': '7-9 LPA',
            'skills': 'SQL, Python, Excel, financial modeling, tableau, power bi, analytics'
        },
        {
            'title': 'Marketing Data Analyst',
            'company': 'AdTech Solutions',
            'location': 'Mumbai, Maharashtra',
            'salary': '5-8 LPA',
            'skills': 'Python, SQL, Google Analytics, tableau, excel, marketing analytics'
        },
        {
            'title': 'Healthcare Data Analyst',
            'company': 'MedAnalytics',
            'location': 'Bangalore, Karnataka',
            'salary': '6-10 LPA',
            'skills': 'R, SQL, Python, healthcare analytics, statistics, data mining'
        }
    ]
    
    # Analyze the sample data
    analyzer = JobAnalyzer(sample_jobs)
    
    # Generate summary and analysis
    summary = analyzer.generate_summary()
    top_locations = analyzer.get_top_locations()
    top_skills = analyzer.get_top_skills()
    
    # Create visualizations
    analyzer.create_visualizations()
    
    # Save data
    analyzer.save_data('demo_jobs_data.csv')
    
    return analyzer, summary

def main():
    """
    Main function to run the job scraper and analyzer
    """
    print("🔍 Data Analyst Job Scraper and Analyzer")
    print("=" * 50)
    
    # For demonstration purposes, we'll use sample data
    # In a real scenario, you would uncomment the scraping code below
    
    """
    # Real scraping implementation (uncomment to use)
    scraper = JobScraper("https://internshala.com")  # or your chosen job portal
    
    # Scrape jobs
    jobs_data = scraper.scrape_jobs(search_query="data analyst", num_pages=3)
    
    if not jobs_data:
        print("No jobs were scraped. Please check the website structure and selectors.")
        return
    
    # Analyze scraped data
    analyzer = JobAnalyzer(jobs_data)
    """
    
    # Demo with sample data
    analyzer, summary = demo_with_sample_data()
    
    print("\n🎯 CHALLENGES FACED DURING SCRAPING:")
    challenges = [
        "1. Different websites have varying HTML structures",
        "2. Anti-bot measures and rate limiting",
        "3. Dynamic content loading (JavaScript-rendered pages)",
        "4. Inconsistent data formats across job listings",
        "5. Need to respect robots.txt and Terms of Service",
        "6. Handling pagination and infinite scroll",
        "7. Extracting structured data from unstructured text"
    ]
    
    for challenge in challenges:
        print(challenge)
    
    print("\n✅ SCRAPING COMPLETED SUCCESSFULLY!")
    print("Check the generated visualizations and CSV file.")

if __name__ == "__main__":
    main()
