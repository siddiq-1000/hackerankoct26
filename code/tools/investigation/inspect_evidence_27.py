import sys
sys.path.insert(0, '.')
from code.evidence.docs import DocumentParser
from pathlib import Path

parser = DocumentParser()
txt = parser.extract_text_from_pdf(Path('dataset/evidence/documents/legal_retention_register_20260529.pdf'))
print("Matches in evidence_27:")
for line in txt.splitlines():
    if any(k in line.lower() for k in ['case_', 'user_', '@', 'legal_hold']):
        print(line.encode('ascii', 'ignore').decode())
