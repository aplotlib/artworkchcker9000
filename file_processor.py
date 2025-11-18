import io
from PIL import Image
import fitz  # PyMuPDF
import streamlit as st

class FileProcessor:
    @staticmethod
    def process_file(uploaded_file):
        """
        Returns: (extracted_text, image_data_list, preview_image_object)
        """
        if not uploaded_file:
            return None, None, None

        filename = uploaded_file.name
        file_bytes = uploaded_file.getvalue()
        
        text_content = ""
        image_parts = []
        preview_img = None

        try:
            if filename.lower().endswith('.pdf'):
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                
                # Get Text
                for page in doc:
                    text_content += page.get_text() + "\n"
                
                # Get Image of First Page for AI/Preview
                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom
                    img_data = pix.tobytes("png")
                    preview_img = Image.open(io.BytesIO(img_data))
                    image_parts = [{"mime_type": "image/png", "data": img_data}]
            
            else: # Images
                image = Image.open(uploaded_file)
                preview_img = image
                image_parts = [{"mime_type": uploaded_file.type, "data": file_bytes}]
                text_content = "Image file. Text extraction will be performed by AI."

        except Exception as e:
            st.error(f"Error processing file: {e}")
            return None, None, None

        return text_content, image_parts, preview_img
