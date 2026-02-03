import fitz

def create_test_pdf():
    doc = fitz.open()
    page = doc.new_page()
    
    # 1. Normal space
    page.insert_text((50, 50), "Issue No: 1", fontsize=12)
    
    # 2. Double space
    page.insert_text((50, 100), "Issue No:  2", fontsize=12)
    
    # 3. Non-breaking space (ASCII 160)
    text_nbsp = "Issue No:\xa03"
    page.insert_text((50, 150), text_nbsp, fontsize=12)
    
    # 4. Separate blocks (simulating table cells)
    # Note: insert_text calls create separate blocks usually
    page.insert_text((50, 200), "Issue No:", fontsize=12)
    page.insert_text((110, 200), "4", fontsize=12)
    
    doc.save("test_spacing.pdf")
    doc.close()

def test_search():
    doc = fitz.open("test_spacing.pdf")
    page = doc[0]
    
    print("Testing search_for...")
    
    # Case sensitivity
    print(f"Search 'issue no: 1' (lowercase): {len(page.search_for('issue no: 1'))} hits")
    
    # Separate blocks
    # "Issue No:" is at (50, 200), "4" is at (110, 200). 
    # They are separate text objects.
    # PyMuPDF's text extraction joins them if they are close?
    print(f"Search 'Issue No: 4' (separate blocks): {len(page.search_for('Issue No: 4'))} hits")
    
    # Check text extraction
    print(f"Page Text:\n{page.get_text('text')}")

if __name__ == "__main__":
    create_test_pdf()
    test_search()
