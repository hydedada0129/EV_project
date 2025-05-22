'''
 Embed the original image into Excel and scale it visually (without resizing file)

If your Excel viewer (e.g., LibreOffice or Excel) supports it, you can:

    Keep the original image file at full resolution

    Insert it into Excel using openpyxl

    Set the image size directly using img.width and img.height
    '''

from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from PIL import Image as PILImage

# Load original image to get size
img_path = "pic_7PNG.png"

with PILImage.open(img_path) as pil_img:
    orig_width, orig_height = pil_img.size

# Target bounding box
max_width = 400
max_height = 320

# Calculate scale factor (keep aspect ratio)
scale_w = max_width / orig_width
scale_h = max_height / orig_height
scale_factor = min(scale_w, scale_h)

# Compute new size
new_width = int(orig_width * scale_factor)
new_height = int(orig_height * scale_factor)

# Create Excel image
img = ExcelImage(img_path)
img.width = new_width
img.height = new_height

# Add to worksheet
wb = Workbook()
ws = wb.active
ws.add_image(img, "B2")

# Save workbook
wb.save("output_scaled.xlsx")
