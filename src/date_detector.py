import re
from dateutil import parser

class DateDetector:
    def __init__(self):
        # Regex patterns for different date formats
        self.patterns = [
            # Numeric: DD/MM/YYYY, DD.MM.YYYY, DD-MM-YYYY
            r'\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
            
            # Numeric: YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD
            r'\b\d{4}[/.-]\d{1,2}[/.-]\d{1,2}\b',
            
            # Space separated: DD MM YYYY (Strict 4 digit year)
            r'\b\d{1,2}\s\d{1,2}\s\d{4}\b',

            # DD Month YYYY (e.g. 01-Jan-2025, 1 Jan 2025, 1.Jan.2025)
            r'\b\d{1,2}[-.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-.\s,]+\d{2,4}\b',

            # Month DD, YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}[-.\s,]+\d{4}\b',
            
            # Financial Year YYYY-YY
            r'\b\d{4}[–-]\d{2}\b'
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.patterns]

    def find_dates(self, text):
        """
        Finds dates in the given text.
        Returns a list of dictionaries with 'text', 'start', 'end'.
        """
        matches = []
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                matches.append({
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Remove duplicates or overlapping matches
        matches.sort(key=lambda x: x['start'])
        
        unique_matches = []
        if matches:
            current_match = matches[0]
            unique_matches.append(current_match)
            for next_match in matches[1:]:
                if next_match['start'] >= current_match['end']:
                    unique_matches.append(next_match)
                    current_match = next_match
                else:
                    # If overlap, prefer the longer one
                    if len(next_match['text']) > len(current_match['text']):
                        unique_matches.pop()
                        unique_matches.append(next_match)
                        current_match = next_match
                        
        return unique_matches
