"""
File Reader Tool - Downloads and extracts IMD PDF bulletins
Uses LangChain @tool decorator for LangGraph compatibility
"""

from langchain.tools import tool
import requests
from PyPDF2 import PdfReader
from io import BytesIO


# IMD PDF URLs (Bhubaneswar Regional Center)
IMD_PDFS = {
    "evening": "https://mausam.imd.gov.in/bhubaneswar/mcdata/Evening.pdf",
    "rainfall": "https://mausam.imd.gov.in/bhubaneswar/mcdata/daily.pdf",
    "coastal_warning": "https://mausam.imd.gov.in/bhubaneswar/mcdata/coastal.pdf",
    "weekly_rainfall": "https://mausam.imd.gov.in/bhubaneswar/mcdata/weekly.pdf",
    "fishermen_warning": "https://mausam.imd.gov.in/bhubaneswar/mcdata/fishermen.pdf",
    "composite_bulletin": "https://mausam.imd.gov.in/bhubaneswar/mcdata/composite.pdf"
}


@tool
def imd_pdf_reader(pdf_type: str = "all") -> str:
    """
    Download and extract text from IMD PDF bulletins.
    
    Fetches latest weather bulletins from IMD Bhubaneswar and extracts
    first-page summaries for quick information access.
    
    Args:
        pdf_type: Type of PDF to fetch. Options:
            - "all": All bulletins (default)
            - "evening": Evening bulletin
            - "rainfall": Daily rainfall data
            - "coastal_warning": Coastal warnings
            - "weekly_rainfall": Weekly rainfall summary
            - "fishermen_warning": Fishermen advisories
            - "composite_bulletin": Composite bulletin
            
    Returns:
        Extracted text from PDF(s)
        
    Examples:
        imd_pdf_reader("evening")
        imd_pdf_reader("coastal_warning")
        imd_pdf_reader("all")
    """
    pdf_type = pdf_type.lower().strip()
    
    if pdf_type == "all":
        return _get_all_pdf_summaries()
    
    elif pdf_type in IMD_PDFS:
        url = IMD_PDFS[pdf_type]
        text = _download_and_extract(url)
        return f"[{pdf_type.upper().replace('_', ' ')}]\n\n{text}"
    
    else:
        available = ", ".join(IMD_PDFS.keys())
        return f"Error: Unknown PDF type '{pdf_type}'. Available: {available}, all"


def _get_all_pdf_summaries() -> str:
    """
    Download all IMD PDFs and extract first-page summaries.
    
    Returns:
        Combined text from all PDF first pages
    """
    output = []
    output.append("=" * 60)
    output.append("IMD ODISHA WEATHER BULLETINS SUMMARY")
    output.append("=" * 60)
    
    for name, url in IMD_PDFS.items():
        output.append(f"\n{'='*60}")
        output.append(f"[{name.upper().replace('_', ' ')}]")
        output.append(f"{'='*60}")
        
        text = _download_and_extract(url)
        output.append(text)
    
    return "\n".join(output)


def _download_and_extract(url: str, max_pages: int = 1) -> str:
    """
    Download PDF and extract text from first page(s).
    
    Args:
        url: PDF URL
        max_pages: Number of pages to extract (default: 1)
        
    Returns:
        Extracted text or error message
    """
    try:
        # Download PDF
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            return f"❌ HTTP {response.status_code} - Could not download"
        
        # Read PDF from bytes
        pdf_file = BytesIO(response.content)
        reader = PdfReader(pdf_file)
        
        # Check if PDF has pages
        if len(reader.pages) == 0:
            return "❌ PDF is empty"
        
        # Extract text from first page(s)
        extracted_text = []
        
        for i in range(min(max_pages, len(reader.pages))):
            page_text = reader.pages[i].extract_text()
            
            if page_text:
                extracted_text.append(page_text)
        
        if not extracted_text:
            return "❌ Could not extract text from PDF"
        
        return "\n\n".join(extracted_text).strip()
    
    except requests.Timeout:
        return "❌ Download timeout - Server not responding"
    
    except requests.RequestException as e:
        return f"❌ Network error: {str(e)}"
    
    except Exception as e:
        return f"❌ PDF processing error: {str(e)}"