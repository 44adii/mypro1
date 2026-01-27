# legal_drafter_task.py

from crewai import Task

from agents.legal_drafter_agent import legal_drafter_agent
from tasks.case_intake_task import case_intake_task
from tasks.ipc_section_task import ipc_section_task
from tasks.legal_precedent_task import legal_precedent_task
from tasks.advisory_task import advisory_task

legal_drafter_task = Task(
    agent=legal_drafter_agent,
    description=(
        "Review the 'recommended_action' and 'legal_type' from the Advisory Task output.\n"
        "Draft the EXACT document requested (e.g., if 'File FIR' -> Draft an FIR application; if 'Legal Notice' -> Draft a Legal Notice).\n"
        "Incorporate the identified IPC sections and Precedents.\n\n"
        "CRITICAL LANGUAGE RULES: The user's language preference is: {language_preference}\n"
        "- If 'hindi': write the whole document in natural, formal Hindi.\n"
        "- If 'english': write the whole document in English.\n"
        "- If 'both': write in English with short Hindi translation lines immediately after each bullet/section.\n\n"
        "STRICT FORMAT: Output should be clean Markdown with headings and bullet points (no code fences). Use the following structure and keep it concise and clear:\n"
        "# [DOCUMENT TITLE CASED ON ADVISORY]\n"
        "- **Date**: [Current Date]\n"
        "- **Parties**: [Complainant] vs [Respondent]\n\n"
        "## Factual Summary\n"
        "- [1–3 short bullets]\n\n"
        "## Applicable IPC Sections\n"
        "- [Section Number]: [Short Title] — [Why applicable]\n"
        "- [Section Number]: [Short Title] — [Why applicable]\n\n"
        "## Demand / Request\n"
        "- [What action is requested and preferred timeline]\n\n"
        "## Sender Details\n"
        "- [Name], [Address], [Contact]\n"
    ),
    expected_output=(
        "Markdown document with headings and bullet points matching the structure above, fully in the chosen language."
    ),
    context=[case_intake_task, advisory_task, ipc_section_task, legal_precedent_task]
)
