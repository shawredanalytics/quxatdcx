import fitz
from .date_detector import DateDetector

class PDFHandler:
    def __init__(self):
        self.detector = DateDetector()
        self.doc = None
        self.detected_dates = [] 

    def load_pdf(self, stream):
        """Loads PDF from bytes stream"""
        # fitz.open can read from bytes if stream is provided, but it expects specific args
        # stream must be bytes. filetype="pdf" is needed.
        self.doc = fitz.open(stream=stream, filetype="pdf")

    def detect_dates(self):
        """Scans the PDF for dates"""
        self.detected_dates = []
        if not self.doc:
            return []

        for page_num, page in enumerate(self.doc):
            text = page.get_text("text")
            matches = self.detector.find_dates(text)
            
            for match in matches:
                date_text = match['text']
                # Search for the exact location on the page
                hits = page.search_for(date_text)
                
                for rect in hits:
                    # Get context
                    context = self._get_context(text, match['start'], match['end'])
                    
                    self.detected_dates.append({
                        "id": len(self.detected_dates),
                        "page": page_num + 1,
                        "original_text": date_text,
                        "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "replacement": date_text, 
                        "context": context
                    })
        return self.detected_dates

    def _get_context(self, text, start, end, window=30):
        s = max(0, start - window)
        e = min(len(text), end + window)
        return text[s:e].replace('\n', ' ').strip()

    def _get_font_info(self, page, rect):
        """Estimate font size, color, and font name from the rect"""
        default = {"size": 11, "color": (0, 0, 0), "font": "helv"}
        try:
            # We look at the area of the rect
            blocks = page.get_text("dict", clip=rect)["blocks"]
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            # Convert color int to rgb tuple
                            c = s["color"]
                            r = ((c >> 16) & 0xFF) / 255.0
                            g = ((c >> 8) & 0xFF) / 255.0
                            b = (c & 0xFF) / 255.0
                            
                            font_name = s["font"].lower()
                            mapped_font = "helv"
                            if "times" in font_name or "roman" in font_name:
                                mapped_font = "Times-Roman"
                            elif "courier" in font_name or "mono" in font_name:
                                mapped_font = "Courier"
                            
                            return {
                                "size": s["size"],
                                "color": (r, g, b),
                                "font": mapped_font
                            }
        except Exception:
            pass
        return default

    def replace_logo(self, logo_stream, rect=None):
        """
        Replaces or inserts a logo on all pages.
        If rect is None, it tries to find an image in the top-left area.
        """
        if not self.doc:
            return

        # Iterate through all pages to replace logo globally
        for i, page in enumerate(self.doc):
            images = page.get_images()
            target_rect = None
            
            if images:
                # Check if any image is in the top header (e.g., top 150 pixels)
                for img in images:
                    xref = img[0]
                    # Get image bbox
                    img_rects = page.get_image_rects(xref)
                    for r in img_rects:
                        if r.y0 < 150: # Assuming logo is in the top 150 units
                            target_rect = r
                            # Remove original image
                            page.delete_image(xref)
                            break
                    if target_rect:
                        break
            
            if not target_rect:
                # If no logo found, only insert default on first page
                if i == 0:
                    target_rect = fitz.Rect(30, 30, 130, 130) # 100x100 box
                else:
                    continue
                
            # Insert new logo
            page.insert_image(target_rect, stream=logo_stream)

    def replace_text_globally(self, old_text, new_text):
        """
        Replaces all occurrences of old_text with new_text across the document.
        Returns the number of replacements made.
        """
        if not self.doc or not old_text or not new_text:
            return 0

        count = 0
        for page in self.doc:
            hits = page.search_for(old_text)
            if hits:
                for rect in hits:
                    # Get font info
                    font_info = self._get_font_info(page, rect)
                    
                    # Redact
                    page.add_redact_annot(rect, text="")
                    page.apply_redactions(images=0, graphics=0)
                    
                    # Insert
                    try:
                        page.insert_text(
                             (rect.x0, rect.y1 - (rect.height * 0.2)), 
                             new_text, 
                             fontsize=font_info["size"], 
                             fontname=font_info["font"],
                             color=font_info["color"]
                        )
                    except Exception:
                        page.insert_text(
                             (rect.x0, rect.y1 - (rect.height * 0.2)), 
                             new_text, 
                             fontsize=font_info["size"], 
                             fontname="helv",
                             color=font_info["color"]
                        )
                    count += 1
        return count

    def get_page_text(self, page_num=0):
        """Returns the text of a specific page for debugging."""
        if self.doc and 0 <= page_num < len(self.doc):
            return self.doc[page_num].get_text("text")
        return ""

    def apply_changes(self, updates, logo_stream=None, text_replacements=None):
        """
        Applies date replacements, logo change, and generic text replacements.
        text_replacements: list of tuples (old_text, new_text)
        """
        # 1. Apply Date Updates
        update_map = {u['id']: u['replacement'] for u in updates}
        
        for item in self.detected_dates:
            new_text = update_map.get(item['id'])
            if new_text and new_text != item['original_text']:
                page = self.doc[item['page'] - 1]
                rect = fitz.Rect(item['rect'])
                font_info = self._get_font_info(page, rect)
                
                page.add_redact_annot(rect, text="")
                page.apply_redactions(images=0, graphics=0)
                
                try:
                    page.insert_text((rect.x0, rect.y1 - (rect.height * 0.2)), new_text, fontsize=font_info["size"], fontname=font_info["font"], color=font_info["color"])
                except Exception:
                    page.insert_text((rect.x0, rect.y1 - (rect.height * 0.2)), new_text, fontsize=font_info["size"], fontname="helv", color=font_info["color"])

        # 2. Apply Text Replacements (Hospital Name, Document No, etc.)
        replacement_report = {}
        if text_replacements:
            for old_text, new_text in text_replacements:
                count = self.replace_text_globally(old_text, new_text)
                replacement_report[old_text] = count

        # 3. Apply Logo Replacement
        if logo_stream:
            self.replace_logo(logo_stream)

        return self.doc.tobytes(), replacement_report

    def close(self):
        if self.doc:
            self.doc.close()
