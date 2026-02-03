from PIL import Image, ImageStat
from collections import Counter
import os

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

try:
    path = r"C:\Users\MANIKUMAR\Desktop\QuXAT DCX\PDF_Date_Modifier\assets\logo.png"
    img = Image.open(path)
    img = img.convert("RGB")
    
    pixels = list(img.getdata())
    # Filter out white-ish background
    pixels = [p for p in pixels if not (p[0] > 200 and p[1] > 200 and p[2] > 200)]
    
    if not pixels:
        print("Only light pixels found.")
    else:
        counts = Counter(pixels)
        print("Top 10 Colors:")
        for color, count in counts.most_common(10):
            print(f"{rgb_to_hex(color)} - Count: {count}")

except Exception as e:
    print(e)
