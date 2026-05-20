# analyzer/nlp_engine.py
# spaCy-based skill extraction and resume signal detection

import spacy
import re

nlp = spacy.load('en_core_web_sm')

# Master skill dictionary — grouped by domain
SKILL_DICT = {
    # Programming languages
    'python', 'java', 'javascript', 'c++', 'c#', 'r', 'go', 'rust',
    'typescript', 'kotlin', 'swift', 'scala', 'php', 'ruby',

    # Web
    'html', 'css', 'react', 'angular', 'vue', 'node.js', 'django',
    'flask', 'fastapi', 'spring', 'express',

    # Data / ML / AI
    'machine learning', 'deep learning', 'nlp', 'computer vision',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas',
    'numpy', 'matplotlib', 'seaborn', 'opencv', 'huggingface',

    # Data Engineering
    'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
    'hadoop', 'spark', 'kafka', 'airflow', 'dbt',

    # Cloud / DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
    'ci/cd', 'jenkins', 'github actions', 'linux', 'bash',

    # Tools / Practices
    'git', 'github', 'jira', 'agile', 'scrum', 'rest api',
    'graphql', 'microservices', 'system design',

    # Analytics
    'tableau', 'power bi', 'excel', 'looker', 'data visualization',
    'statistics', 'hypothesis testing', 'a/b testing'
}

# Skills required per job role
ROLE_SKILL_MAP = {
    'Data Scientist':       ['python', 'machine learning', 'statistics', 'pandas', 'scikit-learn', 'sql', 'tensorflow'],
    'ML Engineer':          ['python', 'tensorflow', 'pytorch', 'docker', 'kubernetes', 'mlops', 'aws', 'scikit-learn'],
    'Data Analyst':         ['sql', 'python', 'excel', 'tableau', 'power bi', 'statistics', 'data visualization'],
    'Backend Developer':    ['python', 'java', 'sql', 'rest api', 'docker', 'git', 'microservices', 'postgresql'],
    'Frontend Developer':   ['javascript', 'react', 'html', 'css', 'typescript', 'git', 'vue'],
    'Full Stack Developer': ['javascript', 'react', 'node.js', 'python', 'sql', 'docker', 'git', 'rest api'],
    'DevOps Engineer':      ['docker', 'kubernetes', 'aws', 'terraform', 'ci/cd', 'linux', 'bash', 'jenkins'],
    'Cloud Engineer':       ['aws', 'azure', 'gcp', 'terraform', 'docker', 'kubernetes', 'linux'],
    'Data Engineer':        ['python', 'sql', 'spark', 'kafka', 'airflow', 'hadoop', 'aws', 'dbt'],
    'AI Researcher':        ['python', 'pytorch', 'tensorflow', 'deep learning', 'nlp', 'mathematics', 'research']
}


def extract_skills(text: str) -> list[str]:
    """Return list of skills found in text."""
    text_lower = text.lower()
    found = []
    for skill in SKILL_DICT:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def extract_experience_level(text: str) -> str:
    """Estimate experience level from text signals."""
    text_lower = text.lower()

    patterns_senior = [r'\b(8|9|10|\d{2})\+?\s*years?\b', r'\bsenior\b', r'\blead\b', r'\bprincipal\b', r'\bstaff\b']
    patterns_mid    = [r'\b(4|5|6|7)\s*years?\b', r'\bmid[\s-]level\b']
    patterns_junior = [r'\b(1|2|3)\s*years?\b', r'\bjunior\b', r'\bassociate\b']
    patterns_fresh  = [r'\bfresher\b', r'\bgraduate\b', r'\bintern\b', r'\bentry[\s-]level\b', r'\bno experience\b']

    for p in patterns_senior:
        if re.search(p, text_lower): return 'Senior'
    for p in patterns_mid:
        if re.search(p, text_lower): return 'Mid-level'
    for p in patterns_junior:
        if re.search(p, text_lower): return 'Junior'
    for p in patterns_fresh:
        if re.search(p, text_lower): return 'Fresher'
    return 'Not specified'


def extract_entities(text: str) -> dict:
    """Run spaCy NER — return organizations and misc entities."""
    doc = nlp(text[:5000])  # limit for speed
    orgs  = list({ent.text for ent in doc.ents if ent.label_ == 'ORG'})
    misc  = list({ent.text for ent in doc.ents if ent.label_ in ('PRODUCT', 'WORK_OF_ART')})
    return {'organizations': orgs[:8], 'misc': misc[:5]}