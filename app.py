# app.py — Flask application entry point

from flask import Flask, request, jsonify, render_template
from analyzer.parser    import extract_text
from analyzer.nlp_engine import extract_skills, extract_experience_level
from analyzer.scorer    import score_roles, compute_ats_score, get_missing_skills, generate_tips
import re

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    resume_text = ''
    jd_text     = request.form.get('job_description', '').strip()

    # --- Extract resume text ---
    if 'file' in request.files and request.files['file'].filename:
        try:
            resume_text = extract_text(request.files['file'])
        except Exception as e:
            return jsonify({'error': f'File parsing failed: {str(e)}'}), 400
    else:
        resume_text = request.form.get('resume_text', '').strip()

    if len(resume_text) < 50:
        return jsonify({'error': 'Resume text is too short. Please provide more content.'}), 400

    # --- NLP Analysis ---
    found_skills     = extract_skills(resume_text)
    experience_level = extract_experience_level(resume_text)

    # --- Role Matching ---
    role_matches = score_roles(resume_text, jd_text)
    top_role     = role_matches[0]['role'] if role_matches else 'Unknown'

    # --- ATS Score ---
    ats_result   = compute_ats_score(resume_text, found_skills, role_matches, jd_text)

    # --- Missing Skills ---
    missing_skills = get_missing_skills(found_skills, top_role, jd_text)

    # --- Structure hints for tips ---
    resume_lower = resume_text.lower()
    structure = {
        'has_summary':  any(w in resume_lower for w in ['summary', 'objective', 'profile']),
        'has_metrics':  bool(re.search(r'\d+\s*%|\d+x|\$\d+', resume_text)),
        'has_projects': 'project' in resume_lower
    }

    # --- Tips ---
    tips = generate_tips(found_skills, missing_skills, ats_result['score'], structure)

    # --- Response ---
    return jsonify({
        'ats_score':        ats_result['score'],
        'verdict':          ats_result['verdict'],
        'ats_detail':       ats_result['detail'],
        'top_role':         top_role,
        'experience_level': experience_level,
        'role_matches':     role_matches[:6],
        'found_skills':     found_skills,
        'missing_skills':   missing_skills,
        'tips':             tips
    })


if __name__ == '__main__':
    app.run(debug=True)