import requests
import base64
import pandas as pd
import re
import os
from openpyxl import Workbook
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# GitHub API details (update token as needed)
GITHUB_TOKEN = "0e9fccf1923a6b0401e9daf7e55b51c8aa022e20"
ORG_NAME = "CenturyLink"
BRANCH_NAME = "release/february26"  # Update as needed
BASE_URL = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}GITHUB_REPO=your-org/


# Error patterns to extract error messages - more generic
ERROR_PATTERNS = [
    # LoggingUtil.logError patterns
    r'LoggingUtil\.logError\([^,]+,\s*[^,]+,\s*"([^"]+)"',
    r'LoggingUtil\.logError\([^,]+,\s*[^,]+,\s*([^)]+)\)',
    
    # Exception throwing patterns (generic)
    r'throw\s+new\s+\w+Exception\s*\([^)]*"([^"]+)"[^)]*\)',
    r'throw\s+new\s+\w+Exception\s*\([^)]+\)',
    
    # Exception returning patterns (generic)
    r'return\s+new\s+\w+Exception\s*\([^)]*"([^"]+)"[^)]*\)',
    r'return\s+new\s+\w+Exception\s*\([^)]+\)',
    
    # ExceptionHandler patterns
    r'exceptionHandler\.\w+\([^,]+,\s*[^,]+,\s*[^,]+,\s*"([^"]+)"',
]

# Helper to fetch all Java files from the repo (excluding test files)
def get_java_files(org, repo, branch):
    url = f"{BASE_URL}/repos/{org}/{repo}/git/trees/{branch}?recursive=1"
    logging.info(f"Fetching Java files from repo tree: {repo}@{branch}")
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        logging.error(f"Failed to fetch repo tree: {r.text}")
        return []
    tree = r.json().get("tree", [])
    java_files = [item["path"] for item in tree if item["path"].endswith(".java") and "Test" not in item["path"]]
    logging.info(f"Found {len(java_files)} Java files in repo (excluding tests).")
    return java_files

# Helper to fetch file content from GitHub
def fetch_file_content(org, repo, branch, path):
    url = f"{BASE_URL}/repos/{org}/{repo}/contents/{path}?ref={branch}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        logging.warning(f"Failed to fetch file {path}: {r.status_code}")
        return None
    content = r.json().get("content", "")
    return base64.b64decode(content).decode("utf-8")

# Cache for file contents to avoid re-fetching
_file_content_cache = {}

def fetch_file_content_cached(org, repo, branch, path):
    """Cached version of fetch_file_content to avoid duplicate API calls."""
    cache_key = f"{org}/{repo}/{branch}/{path}"
    if cache_key not in _file_content_cache:
        _file_content_cache[cache_key] = fetch_file_content(org, repo, branch, path)
    return _file_content_cache[cache_key]

# Find Java class with @Component("delegateExpression") annotation
def find_class_for_delegate(all_java_files, delegate_expression, main_repo, dependency_repos, file_content_cache=None):
    """
    Search for a class with @Component("delegateExpression") - OPTIMIZED VERSION.
    
    OPTIMIZATIONS:
    1. Searches only delegate/service files first (common naming patterns)
    2. Uses GitHub Code Search API as fallback (much faster)
    3. Caches file contents
    4. Prioritizes main repo, then dependencies
    
    Args:
        all_java_files: Dict of {repo: [file_paths]}
        delegate_expression: The delegate name to search for
        main_repo: Main repo name to search first
        dependency_repos: List of dependency repo names
        file_content_cache: Optional dict to cache file contents
    
    Returns:
        tuple: (repo_name, file_path, class_name, content) or (None, None, None, None)
    """
    logging.info(f"🔍 Searching for @Component(\"{delegate_expression}\")...")
    
    # Use cache if provided
    if file_content_cache is None:
        file_content_cache = {}
    
    # Search order: main repo first, then dependencies
    search_order = [main_repo] + dependency_repos
    
    # OPTIMIZATION 1: Try GitHub Code Search API first (much faster!)
    try:
        search_query = f'@Component("{delegate_expression}") org:{ORG_NAME} language:java'
        for repo in search_order:
            search_query_repo = f'{search_query} repo:{ORG_NAME}/{repo}'
            search_url = f"{BASE_URL}/search/code?q={requests.utils.quote(search_query_repo)}"
            r = requests.get(search_url, headers=HEADERS, timeout=5)
            
            if r.status_code == 200:
                results = r.json().get("items", [])
                if results:
                    # Found via search! Get the file content
                    item = results[0]
                    path = item["path"]
                    logging.info(f"⚡ Found via GitHub Search in {repo}: {path}")
                    
                    cache_key = f"{ORG_NAME}/{repo}/{BRANCH_NAME}/{path}"
                    if cache_key not in file_content_cache:
                        file_content_cache[cache_key] = fetch_file_content(ORG_NAME, repo, BRANCH_NAME, path)
                    content = file_content_cache[cache_key]
                    
                    if content:
                        class_match = re.search(r'^\s*(public\s+)?(class|interface|enum)\s+(\w+)', content, re.MULTILINE)
                        if class_match:
                            class_name = class_match.group(3)
                            logging.info(f"✅ Found in {repo}: {class_name} ({path})")
                            return repo, path, class_name, content
    except Exception as e:
        logging.debug(f"GitHub Search API failed (will fall back to file-by-file): {e}")
    
    # OPTIMIZATION 2: If search API didn't work, search only likely files first
    delegate_lower = delegate_expression.lower()
    for repo in search_order:
        java_files = all_java_files.get(repo, [])
        
        # First pass: Check files that likely contain delegates (naming convention)
        likely_files = [f for f in java_files if any(keyword in f.lower() for keyword in 
                       ['delegate', 'service', 'task', 'handler', 'worker', 'activity'])]
        
        for path in likely_files:
            cache_key = f"{ORG_NAME}/{repo}/{BRANCH_NAME}/{path}"
            if cache_key not in file_content_cache:
                file_content_cache[cache_key] = fetch_file_content(ORG_NAME, repo, BRANCH_NAME, path)
            content = file_content_cache[cache_key]
            
            if not content:
                continue
            
            # Search for @Component annotation with the delegate expression
            if re.search(rf'@Component\s*\(\s*["\']{{1}}{re.escape(delegate_expression)}["\']{{1}}\s*\)', content):
                class_match = re.search(r'^\s*(public\s+)?(class|interface|enum)\s+(\w+)', content, re.MULTILINE)
                if class_match:
                    class_name = class_match.group(3)
                    logging.info(f"✅ Found in {repo}: {class_name} ({path})")
                    return repo, path, class_name, content
    
    # OPTIMIZATION 3: Last resort - search all remaining files (not already checked)
    for repo in search_order:
        java_files = all_java_files.get(repo, [])
        likely_files = set(f for f in java_files if any(keyword in f.lower() for keyword in 
                          ['delegate', 'service', 'task', 'handler', 'worker', 'activity']))
        
        for path in java_files:
            if path in likely_files:
                continue  # Already checked
            
            cache_key = f"{ORG_NAME}/{repo}/{BRANCH_NAME}/{path}"
            if cache_key not in file_content_cache:
                file_content_cache[cache_key] = fetch_file_content(ORG_NAME, repo, BRANCH_NAME, path)
            content = file_content_cache[cache_key]
            
            if not content:
                continue
            
            # Search for @Component annotation
            if re.search(rf'@Component\s*\(\s*["\']{{1}}{re.escape(delegate_expression)}["\']{{1}}\s*\)', content):
                class_match = re.search(r'^\s*(public\s+)?(class|interface|enum)\s+(\w+)', content, re.MULTILINE)
                if class_match:
                    class_name = class_match.group(3)
                    logging.info(f"✅ Found in {repo}: {class_name} ({path})")
                    return repo, path, class_name, content
    
    logging.warning(f"⚠️  No class found for delegate '{delegate_expression}'")
    return None, None, None, None

# Find class from import statement
def find_class_from_import(all_java_files, import_statement, all_repos):
    """
    Find a class based on its import statement (e.g., com.lumen.bm.ordermanagement.delegates.ValidateOrderDelegate)
    
    Args:
        all_java_files: Dict of {repo: [file_paths]}
        import_statement: Full class path from import
        all_repos: List of all repo names
    
    Returns:
        tuple: (repo_name, file_path, class_name, content) or (None, None, None, None)
    """
    # Extract class name from import (last part)
    class_name = import_statement.split('.')[-1]
    
    logging.info(f"🔍 Searching for class from import: {class_name}")
    
    for repo in all_repos:
        java_files = all_java_files.get(repo, [])
        # Look for files that end with the class name
        for path in java_files:
            if path.endswith(f"{class_name}.java"):
                content = fetch_file_content(ORG_NAME, repo, BRANCH_NAME, path)
                if content:
                    logging.info(f"✅ Found via import in {repo}: {class_name} ({path})")
                    return repo, path, class_name, content
    
    return None, None, None, None

# Extract error messages and their method/class context
def extract_errors_with_methods(content, service_name):
    results = []
    lines = content.splitlines()
    current_method = None
    class_name = None
    # Better method pattern - must start with public/private/protected and have return type
    method_pattern = re.compile(r'^\s*(public|private|protected)\s+(static\s+)?[\w\<\>\[\]]+\s+(\w+)\s*\(')
    class_pattern = re.compile(r'^\s*(public\s+)?(class|interface|enum)\s+(\w+)')
    
    for i, line in enumerate(lines):
        # Track class name
        if class_name is None:
            class_match = class_pattern.search(line)
            if class_match:
                class_name = class_match.group(3)
        
        # Track method name - only match actual method declarations
        method_match = method_pattern.search(line)
        if method_match:
            current_method = method_match.group(3)
        
        # Search for error patterns
        for pat in ERROR_PATTERNS:
            for m in re.finditer(pat, line):
                msg = m.group(1) if m.groups() and m.group(1) else m.group(0)
                # Enhance generic error messages
                if msg.strip() in ["Exception", "Error", "Error Message", "Exception Message"] or re.match(r'Exception(\s*\+\s*e\.getMessage\(\))?', msg.strip()):
                    sample_exc = "NullPointerException/IndexOutOfBoundsException"
                    msg = f"{class_name or ''}, {current_method or ''}, Exception - e.getMessage() (Ex:{sample_exc})"
                results.append({
                    "ServiceName": service_name,
                    "ClassName": class_name or "",
                    "MethodName": current_method or "",
                    "ErrorMessage": msg
                })
    return results

def load_bpmn_classes_from_excel(file_path, sheet_name=None, column_name="DelegateExpression"):
    """
    Load BPMN delegate expressions from an Excel file.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet (if None, uses first sheet)
        column_name: Name of the column containing delegate expressions (default: "DelegateExpression")
    
    Returns:
        DataFrame with all columns from the Excel file
    """
    try:
        if not os.path.exists(file_path):
            logging.warning(f"BPMN classes file not found: {file_path}")
            return pd.DataFrame()
        
        logging.info(f"📂 Loading BPMN activities from: {file_path}")
        
        # Read Excel file
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)  # Read first sheet
        
        # Check if DelegateExpression column exists
        if column_name not in df.columns:
            logging.error(f"Column '{column_name}' not found. Available columns: {list(df.columns)}")
            return pd.DataFrame()
        
        # Remove rows with empty delegate expressions
        df = df[df[column_name].notna()]
        
        logging.info(f"✅ Loaded {len(df)} BPMN activities with delegate expressions")
        logging.info(f"📋 Columns: {list(df.columns)}")
        
        return df
    except Exception as e:
        logging.error(f"Error loading BPMN activities from Excel: {e}")
        return pd.DataFrame()

def main():
    overall_start = time.time()
    
    # List of repo names to process (main repos)
    REPO_LIST = [
        "BMOM-om-process-decomposition"
    ]
    
    # List of dependency module repos to process
    DEPENDENCY_REPOS = [
        # Add your dependency module repos here
        "BMOM-order-management-camunda-common"
    ]
    
    # PATTERN SELECTION
    # Pattern 1: Provide BPMN activities file to search specific delegates + all remaining classes in main repo
    # Pattern 2: Set BPMN_CLASSES_FILE to None to search all classes in main repo (and dependencies if specified)
    
    # Path to Excel file containing BPMN activities with DelegateExpression
    # Set to None to skip BPMN pattern and search all classes (Pattern 2)
    BPMN_CLASSES_FILE = "OM_Decomposition_Activities.xlsx"  # Set to None for Pattern 2
    BPMN_SHEET_NAME = "Activities"  # None = use first sheet
    BPMN_COLUMN_NAME = "DelegateExpression"  # Column containing delegate expressions
    
    # For Pattern 1: After processing BPMN delegates, also search remaining classes in main repo?
    SEARCH_REMAINING_CLASSES = True  # Set to False to only process BPMN delegates
    
    # For Pattern 2: Search dependencies even when no BPMN file provided?
    SEARCH_DEPENDENCIES_WITHOUT_BPMN = False  # Set to True to include dependencies in Pattern 2
    
    # Combine all repos to process
    main_repo = REPO_LIST[0]
    
    # Save to current directory with full path
    current_dir = os.getcwd()
    OUTPUT_FILE = os.path.join(current_dir, f"github_errors_{main_repo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    logging.info(f"Output will be saved to: {OUTPUT_FILE}")
    
    # Determine which pattern we're using
    if BPMN_CLASSES_FILE and os.path.exists(BPMN_CLASSES_FILE):
        pattern = "PATTERN 1: BPMN Activities + Remaining Classes"
        all_repos_to_search = [main_repo] + DEPENDENCY_REPOS
    else:
        pattern = "PATTERN 2: All Classes in Main Repo"
        all_repos_to_search = [main_repo] + (DEPENDENCY_REPOS if SEARCH_DEPENDENCIES_WITHOUT_BPMN else [])
    
    logging.info(f"\n{'='*60}")
    logging.info(f"🎯 {pattern}")
    logging.info(f"{'='*60}")
    logging.info(f"Main Repository: {main_repo}")
    logging.info(f"Dependency Repos: {', '.join(DEPENDENCY_REPOS) if DEPENDENCY_REPOS else 'None'}")
    logging.info(f"Searching in: {', '.join(all_repos_to_search)}")
    
    # Step 1: Fetch all Java files from all repos
    logging.info(f"\n{'='*60}")
    logging.info("STEP 1: Fetching Java files from all repositories")
    logging.info(f"{'='*60}")
    
    all_java_files = {}
    for repo in all_repos_to_search:
        fetch_start = time.time()
        java_files = get_java_files(ORG_NAME, repo, BRANCH_NAME)
        all_java_files[repo] = java_files
        fetch_time = time.time() - fetch_start
        logging.info(f"✅ {repo}: {len(java_files)} files ({fetch_time:.2f}s)")
    
    output_rows = []
    processed_classes = set()  # Track which classes we've already processed
    file_content_cache = {}  # Cache for file contents to speed up searches
    
    # PATTERN 1: Process BPMN delegates if file provided
    if BPMN_CLASSES_FILE and os.path.exists(BPMN_CLASSES_FILE):
        # Load BPMN activities from Excel file
        bpmn_df = load_bpmn_classes_from_excel(
            BPMN_CLASSES_FILE, 
            sheet_name=BPMN_SHEET_NAME,
            column_name=BPMN_COLUMN_NAME
        )
        
        if not bpmn_df.empty:
            logging.info(f"\n{'='*60}")
            logging.info("STEP 2A: Processing BPMN Delegate Expressions")
            logging.info(f"{'='*60}")
            
            processed_count = 0
            found_count = 0
            
            for idx, row in bpmn_df.iterrows():
                delegate_expression = row.get(BPMN_COLUMN_NAME)
                processed_count += 1
                
                logging.info(f"\n[{processed_count}/{len(bpmn_df)}] Processing: {delegate_expression}")
                
                if not delegate_expression or pd.isna(delegate_expression):
                    logging.warning("⚠️  Empty delegate expression, skipping")
                    continue
                
                # Search for the class (main repo first, then dependencies) - WITH CACHE
                repo_name, file_path, class_name, content = find_class_for_delegate(
                    all_java_files, 
                    str(delegate_expression).strip(),
                    main_repo,
                    DEPENDENCY_REPOS,
                    file_content_cache  # Pass cache
                )
                
                if not class_name:
                    # Add row with no class found
                    out_row = row.to_dict()
                    out_row["RepoName"] = "NOT_FOUND"
                    out_row["ClassName"] = ""
                    out_row["MethodName"] = ""
                    out_row["ErrorMessage"] = "Class not found"
                    out_row["Source"] = "BPMN"
                    output_rows.append(out_row)
                    continue
                
                found_count += 1
                processed_classes.add((repo_name, class_name))  # Track processed class
                
                # Extract errors from the class
                errors = extract_errors_with_methods(content, repo_name)
                
                if errors:
                    logging.info(f"📊 Extracted {len(errors)} errors from {class_name}")
                    for err in errors:
                        out_row = row.to_dict()
                        out_row["RepoName"] = repo_name
                        out_row["ClassName"] = err["ClassName"] or class_name
                        out_row["MethodName"] = err["MethodName"]
                        out_row["ErrorMessage"] = err["ErrorMessage"]
                        out_row["Source"] = "BPMN"
                        output_rows.append(out_row)
                else:
                    # Add row with class found but no errors
                    logging.info(f"ℹ️  No errors found in {class_name}")
                    out_row = row.to_dict()
                    out_row["RepoName"] = repo_name
                    out_row["ClassName"] = class_name
                    out_row["MethodName"] = ""
                    out_row["ErrorMessage"] = "No errors found"
                    out_row["Source"] = "BPMN"
                    output_rows.append(out_row)
            
            logging.info(f"\n📊 BPMN Processing Summary:")
            logging.info(f"   Processed: {processed_count}, Found: {found_count}, Not Found: {processed_count - found_count}")
    
    # STEP 2B/3: Process remaining classes in main repo (Pattern 1 with SEARCH_REMAINING_CLASSES or Pattern 2)
    if (BPMN_CLASSES_FILE and SEARCH_REMAINING_CLASSES) or (not BPMN_CLASSES_FILE):
        logging.info(f"\n{'='*60}")
        step_name = "STEP 2B: Processing Remaining Classes in Main Repo" if BPMN_CLASSES_FILE else "STEP 2: Processing All Classes"
        logging.info(step_name)
        logging.info(f"{'='*60}")
        
        remaining_count = 0
        main_java_files = all_java_files.get(main_repo, [])
        
        for idx, path in enumerate(main_java_files, 1):
            # Use cached fetch
            cache_key = f"{ORG_NAME}/{main_repo}/{BRANCH_NAME}/{path}"
            if cache_key not in file_content_cache:
                file_content_cache[cache_key] = fetch_file_content(ORG_NAME, main_repo, BRANCH_NAME, path)
            content = file_content_cache[cache_key]
            
            if not content:
                continue
            
            # Extract class name
            class_match = re.search(r'^\s*(public\s+)?(class|interface|enum)\s+(\w+)', content, re.MULTILINE)
            if not class_match:
                continue
            
            class_name = class_match.group(3)
            
            # Skip if already processed from BPMN
            if (main_repo, class_name) in processed_classes:
                continue
            
            remaining_count += 1
            
            # Extract errors
            errors = extract_errors_with_methods(content, main_repo)
            
            if errors:
                for err in errors:
                    out_row = {
                        "RepoName": main_repo,
                        "ClassName": err["ClassName"] or class_name,
                        "MethodName": err["MethodName"],
                        "ErrorMessage": err["ErrorMessage"],
                        "Source": "MainRepo"
                    }
                    output_rows.append(out_row)
            
            if idx % 20 == 0:
                logging.info(f"  Processed {idx}/{len(main_java_files)} files, found {remaining_count} new classes...")
        
        logging.info(f"✅ Processed {remaining_count} additional classes from main repo")
    
    # Final Step: Write to Excel
    if output_rows:
        excel_start = time.time()
        logging.info(f"\n{'='*60}")
        logging.info("FINAL STEP: Writing data to Excel")
        logging.info(f"{'='*60}")
        
        out_df = pd.DataFrame(output_rows)
        out_df.to_excel(OUTPUT_FILE, index=False)
        
        excel_time = time.time() - excel_start
        logging.info(f"⏱️  Excel writing took: {excel_time:.2f} seconds")
        logging.info(f"✅ Output written to {OUTPUT_FILE}")
        logging.info(f"📊 Total rows: {len(output_rows)}")
    else:
        logging.warning("❌ No data to write.")
    
    overall_time = time.time() - overall_start
    logging.info(f"\n{'='*60}")
    logging.info(f"📈 FINAL SUMMARY")
    logging.info(f"{'='*60}")
    logging.info(f"  Pattern Used: {pattern}")
    logging.info(f"  Total output rows: {len(output_rows)}")
    logging.info(f"⏱️  TOTAL EXECUTION TIME: {overall_time:.2f} seconds ({overall_time/60:.2f} minutes)")
    logging.info(f"{'='*60}")

if __name__ == "__main__":
    main()
