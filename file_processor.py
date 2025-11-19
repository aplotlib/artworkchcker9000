import fitz  # PyMuPDF
from PIL import Image
import io
import streamlit as st

class FileProcessor:
    def __init__(self):
        pass

    def process_files(self, uploaded_files):
        """
        Processes a LIST of uploaded files (PDFs or Images).
        Returns combined text, combined image parts, and a preview image.
        """
        all_text = ""
        all_image_parts = []
        preview_image = None

        for uploaded_file in uploaded_files:
            text, parts, preview = self.process_file(uploaded_file)
            
            # Append text with a separator
            if text:
                all_text += f"\n--- FILE: {uploaded_file.name} ---\n{text}"
            
            # Extend image parts
            if parts:
                all_image_parts.extend(parts)
            
            # Keep the first valid preview found
            if not preview_image and preview:
                preview_image = preview

        return all_text, all_image_parts, preview_image

    def process_file(self, uploaded_file):
        """
        Processes a SINGLE file.
        """
        text_content = ""
        image_parts = []
        preview_image = None

        try:
            file_bytes = uploaded_file.read()
            file_type = uploaded_file.type

            # 1. PDF Handling
            if "pdf" in file_type:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                
                # Extract text
                for page in doc:
                    text_content += page.get_text()

                # Convert first page to image for AI/Preview
                # (In production, you might want to convert ALL pages)
                for page_num, page in enumerate(doc):
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    image_parts.append({
                        "mime_type": "image/png",
                        "data": img_data
                    })
                    
                    # Set preview if it's the first page of first file
                    if page_num == 0:
                        preview_image = Image.open(io.BytesIO(img_data))

            # 2. Image Handling
            elif "image" in file_type:
                image = Image.open(io.BytesIO(file_bytes))
                text_content = "[Image File - Text Extraction Not Enabled]"
                preview_image = image
                
                # Convert to bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                image_parts.append({
                    "mime_type": file_type,
                    "data": img_byte_arr.getvalue()
                })

            return text_content, image_parts, preview_image

        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {e}")
            return "", [], None
