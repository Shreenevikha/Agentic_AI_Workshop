import pytesseract
from pdf2image import convert_from_path
import fitz  # PyMuPDF
import cv2
import numpy as np
from typing import Dict, List
import logging
import os
from PIL import Image
import re
from datetime import datetime

# Configure Tesseract path explicitly for Windows
try:
    # This path is the default installation location for Tesseract on Windows.
    # If you installed Tesseract to a different directory, please update this path accordingly.
    pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    logging.getLogger(__name__).info("Tesseract command path set explicitly.")
except Exception as e:
    logging.getLogger(__name__).error(f"Could not set Tesseract command path: {e}")
    logging.getLogger(__name__).warning("Pytesseract might not function correctly if Tesseract is not in PATH.")

class DocumentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff'}
        
        # Define information patterns to look for in documents
        self.info_patterns = {
            'financial': {
                'bank_account': r'(?i)bank\s*account\s*(?:number|no|#)?[:#]?\s*([A-Z0-9\s-]+)',
                'ifsc_code': r'(?i)ifsc\s*(?:code)?[:#]?\s*([A-Z0-9]+)',
                'tax_number': r'(?i)(?:tax|gst|pan)\s*(?:number|no|#)?[:#]?\s*([A-Z0-9]+)',
                'financial_year': r'(?i)(?:fy|financial\s*year)[:#]?\s*(\d{4}[-/]\d{2,4})',
                'turnover': r'(?i)(?:annual\s*)?turnover[:#]?\s*(?:rs\.?|inr)?\s*([\d,]+)',
                'profit': r'(?i)(?:net\s*)?profit[:#]?\s*(?:rs\.?|inr)?\s*([\d,]+)'
            },
            'legal': {
                'registration_number': r'(?i)(?:registration|reg\.?)\s*(?:number|no|#)?[:#]?\s*([A-Z0-9-]+)',
                'incorporation_date': r'(?i)(?:incorporation|inc\.?)\s*date[:#]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                'authorized_capital': r'(?i)authorized\s*capital[:#]?\s*(?:rs\.?|inr)?\s*([\d,]+)',
                'paid_up_capital': r'(?i)paid\s*[- ]up\s*capital[:#]?\s*(?:rs\.?|inr)?\s*([\d,]+)'
            },
            'compliance': {
                'iso_certification': r'(?i)iso\s*(?:certification|cert\.?)?[:#]?\s*([A-Z0-9-]+)',
                'licenses': r'(?i)(?:license|lic\.?)\s*(?:number|no|#)?[:#]?\s*([A-Z0-9-]+)',
                'audit_status': r'(?i)(?:audit|audited)\s*(?:status|report)?[:#]?\s*(clean|qualified|adverse)',
                'compliance_score': r'(?i)compliance\s*score[:#]?\s*(\d+(?:\.\d+)?)'
            },
            'operational': {
                'employee_count': r'(?i)(?:total\s*)?employees[:#]?\s*(\d+)',
                'location': r'(?i)(?:registered\s*)?address[:#]?\s*([^\n]+)',
                'contact_info': r'(?i)(?:contact|phone|mobile|email)[:#]?\s*([^\n]+)',
                'business_type': r'(?i)(?:type\s*of\s*business|business\s*type)[:#]?\s*([^\n]+)'
            }
        }

    def process_documents(self, file_paths: List[str]) -> Dict:
        """
        Process multiple documents and extract text, metadata, and specific information
        
        Args:
            file_paths: List of paths to documents
            
        Returns:
            Dictionary containing processed document data
        """
        processed_docs = []
        
        for file_path in file_paths:
            try:
                file_ext = os.path.splitext(file_path)[1].lower()
                
                if file_ext not in self.supported_extensions:
                    raise ValueError(f"Unsupported file type: {file_ext}")
                
                # Extract metadata
                metadata = self._extract_metadata(file_path)
                
                # Extract text based on file type
                if file_ext == '.pdf':
                    text = self._process_pdf(file_path)
                else:  # Image files
                    text = self._process_image(file_path)
                
                # Extract specific information from text
                extracted_info = self._extract_document_info(text)
                
                processed_docs.append({
                    'file_path': file_path,
                    'metadata': metadata,
                    'extracted_text': text,
                    'extracted_info': extracted_info
                })
                
            except Exception as e:
                self.logger.error(f"Error processing document {file_path}: {str(e)}")
                raise
        
        return {
            'processed_documents': processed_docs,
            'total_documents': len(processed_docs)
        }

    def _extract_document_info(self, text: str) -> Dict:
        """Extract specific information from document text"""
        extracted_info = {
            'financial': {},
            'legal': {},
            'compliance': {},
            'operational': {}
        }
        
        for category, patterns in self.info_patterns.items():
            for info_type, pattern in patterns.items():
                matches = re.finditer(pattern, text)
                values = []
                for match in matches:
                    value = match.group(1).strip()
                    if value:
                        values.append(value)
                if values:
                    extracted_info[category][info_type] = values[0] if len(values) == 1 else values
        
        return extracted_info

    def _extract_metadata(self, file_path: str) -> Dict:
        """Extract metadata from document"""
        file_stats = os.stat(file_path)
        return {
            'filename': os.path.basename(file_path),
            'file_size': file_stats.st_size,
            'created_time': file_stats.st_ctime,
            'modified_time': file_stats.st_mtime
        }

    def _process_pdf(self, file_path: str) -> str:
        """Process PDF document and extract text"""
        try:
            # First try direct text extraction using PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            # If no text found, use OCR
            if not text.strip():
                images = convert_from_path(file_path)
                text = ""
                for image in images:
                    text += self._perform_ocr(image)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error processing PDF {file_path}: {str(e)}")
            # If PyMuPDF fails, try OCR directly
            try:
                images = convert_from_path(file_path)
                text = ""
                for image in images:
                    text += self._perform_ocr(image)
                return text
            except Exception as ocr_error:
                self.logger.error(f"OCR also failed: {str(ocr_error)}")
                raise

    def _process_image(self, file_path: str) -> str:
        """Process image document and extract text using OCR"""
        try:
            # Read image
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError(f"Could not read image file: {file_path}")
            
            # Preprocess image
            image = self._preprocess_image(image)
            
            # Convert to PIL Image for OCR
            pil_image = Image.fromarray(image)
            
            # Perform OCR
            text = self._perform_ocr(pil_image)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error processing image {file_path}: {str(e)}")
            raise

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply thresholding
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Noise removal
            denoised = cv2.fastNlMeansDenoising(binary)
            
            return denoised
        except Exception as e:
            self.logger.error(f"Error preprocessing image: {str(e)}")
            return image  # Return original image if preprocessing fails

    def _perform_ocr(self, image: Image.Image) -> str:
        """Perform OCR on image"""
        try:
            # Configure OCR
            custom_config = r'--oem 3 --psm 6'
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=custom_config)
            
            return text
            
        except Exception as e:
            self.logger.error(f"Error performing OCR: {str(e)}")
            raise 