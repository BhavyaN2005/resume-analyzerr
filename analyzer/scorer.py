# analyzer/scorer.py
# ATS scoring + role matching using TF-IDF cosine similarity

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .nlp_engine import ROLE_SKILL_MAP, extract_skills


def score_roles(resume_text: str, jd_text: str = '') -> list[dict]:
    """
    Score resume against each job role profile using TF-IDF + cosine similarity.
    Returns list of {role, score} sorted by score desc.
    """
    # Build corpus: resume + all role descriptions
    role_names  = list(ROLE_SKILL_MAP.keys())
    role_texts  = [' '.join(skills) for skills in ROLE_SKILL_MAP.values()]

    # If JD provided, blend it into resume for better targeting
    query = resume_text + (' ' + jd_text if jd_text else '')

    corpus = [query] + role_texts

    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Cosine similarity between resume and each role
    resume_vec = tfidf_matrix[0]
    role_vecs  = tfidf_matrix[1:]
    similarities = cosine_similarity(resume_vec, role_vecs)[0]

    results = []
    for name, sim in zip(role_names, similarities):
        results.append({
            'role':  name,
            'score': int(round(sim * 100))
        })

    return sorted(results, key=lambda x: x['score'], reverse=True)


def compute_ats_score(resume_text: str, found_skills: list[str],
                      role_matches: list[dict], jd_text: str = '') -> dict:
    """
    ATS score = weighted combination of:
      - Skill density (40%)
      - Role match strength (30%)
      - Resume length/structure signals (20%)
      - JD alignment if provided (10%)
    """
    # 1. Skill density score
    skill_count   = len(found_skills)
    skill_score   = min(100, skill_count * 5)          # caps at 20 skills = 100

    # 2. Top role match score
    top_match     = role_matches[0]['score'] if role_matches else 0

    # 3. Structure score — check for key sections
    resume_lower  = resume_text.lower()
    sections      = ['experience', 'education', 'skills', 'project', 'summary', 'objective']
    found_sections = sum(1 for s in sections if s in resume_lower)
    structure_score = min(100, found_sections * 17)

    # 4. JD alignment score
    if jd_text:
        jd_skills = extract_skills(jd_text)
        if jd_skills:
            overlap      = len(set(found_skills) & set(jd_skills))
            jd_score     = int(min(100, (overlap / len(jd_skills)) * 100))
        else:
            jd_score = 60
    else:
        jd_score = 60  # neutral when no JD

    # Weighted total
    ats_raw = (
        skill_score   * 0.40 +
        top_match     * 0.30 +
        structure_score * 0.20 +
        jd_score      * 0.10
    )
    ats = int(round(min(100, ats_raw)))

    # Verdict
    if ats >= 80:
        verdict = 'Excellent'
        detail  = 'Your resume is highly ATS-compatible and well-optimized.'
    elif ats >= 65:
        verdict = 'Good'
        detail  = 'Solid resume with a few areas to strengthen.'
    elif ats >= 45:
        verdict = 'Fair'
        detail  = 'Moderate fit — needs skill additions and structure improvements.'
    else:
        verdict = 'Needs Work'
        detail  = 'Low ATS compatibility — significant improvements recommended.'

    return {'score': ats, 'verdict': verdict, 'detail': detail}


def get_missing_skills(found_skills: list[str], top_role: str,
                       jd_text: str = '') -> list[str]:
    """
    Returns skills missing for the top matched role.
    If JD provided, also includes JD-specific missing skills.
    """
    role_required = set(ROLE_SKILL_MAP.get(top_role, []))
    found_set     = set(found_skills)
    missing       = list(role_required - found_set)

    if jd_text:
        jd_skills = set(extract_skills(jd_text))
        jd_missing = list(jd_skills - found_set)
        missing    = list(set(missing + jd_missing))

    return sorted(missing)[:10]   # top 10 missing


def generate_tips(found_skills: list[str], missing_skills: list[str],
                  ats_score: int, structure_hints: dict) -> list[str]:
    """Rule-based improvement tip generator."""
    tips = []

    if ats_score < 50:
        tips.append('Your ATS score is low — add a dedicated Skills section with technology keywords.')

    if len(found_skills) < 8:
        tips.append('List more technical skills explicitly — ATS parsers scan for keyword density.')

    if missing_skills:
        top_missing = ', '.join(missing_skills[:4])
        tips.append(f'Consider learning or adding these to your resume: {top_missing}.')

    if not structure_hints.get('has_summary'):
        tips.append('Add a 2–3 line professional summary at the top for better ATS parsing.')

    if not structure_hints.get('has_metrics'):
        tips.append('Quantify your achievements (e.g. "Reduced load time by 40%") to stand out.')

    if not structure_hints.get('has_projects'):
        tips.append('Add a Projects section showcasing real-world work — especially important for freshers.')

    tips.append('Use standard section headings: Experience, Education, Skills, Projects.')
    tips.append('Save and submit your resume as PDF to preserve formatting for ATS systems.')

    return tips[:6]