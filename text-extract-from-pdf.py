"""
File Name: text_extraction_pipeline.py
Author: Senthilnathan Karuppaiah
Date: 20-Aug-2023
Description: This script creates a Dagster pipeline that chains several data processing functions to extract text from PDFs.
             Function chaining is managed through Dagster's naming conventions, where the output of one function is passed
             to the next by matching the argument name with the previous function's name.
             The initial inputs for the pipeline are provided via a JSON structure when materializing the pipeline.
             The output files from 'split_pdf' are named according to the input file name with page numbers appended.

Note: Update the 'input_file_path' and 'output_file_path' as per your requirements. The 'output_file_path' should be a directory.
      Output files will be named with the page number appended to the input file name, e.g., 'Ilaiya-Raani_1.pdf', 'Ilaiya-Raani_2.pdf', etc.

Requirements:
- dagster
- PyPDF2
- pdf2image
- pytesseract
- PIL
- elasticsearch
- structlog
- python-dotenv
- json


"""

import json
from dagster import AssetIn, asset, Config
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
import os
from pdf2image import convert_from_path
from PIL import Image
from elasticsearch import Elasticsearch
import logging
from datetime import datetime
import structlog
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from a .env file
# Retrieve Elasticsearch configuration from environment variables
ES_CLOUD_ID = os.getenv("ES_CLOUD_ID")
ES_CLOUD_USERNAME = os.getenv("ES_CLOUD_USERNAME")
ES_CLOUD_PASSWORD = os.getenv("ES_CLOUD_PASSWORD")
ES_INDEX_NAME = os.getenv("ES_INDEX_NAME")

# Extract the base name of the script without the directory path or file extension
script_name = os.path.splitext(os.path.basename(__file__))[0]

# Generate a log filename with the current timestamp
log_filename = f"{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(filename=log_filename, level=logging.INFO, format="%(message)s")
structlog.configure(
    logger_factory=structlog.stdlib.LoggerFactory(),
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
log = structlog.get_logger()


# Configuration class for defining asset inputs
class AssetCongigs(Config):
    input_file_path: str
    output_file_path: str
    ocr_lang: str

@asset
def split_pdf(context,config: AssetCongigs):
    """
    Function to split a PDF into individual page files.
    The sequence of function calls is managed by Dagster, where the name of the output from this function 'split_pdf'
    is passed as an argument to the next function in the pipeline.

    Args:
    - context: The Dagster context object for the asset.
    - config: AssetConfigs object containing configurations for the asset.

    Returns:
    - List of paths to the individual PDF page files.
    """

    input_pdf_name = config.input_file_path.split('/')[-1].split('.')[0]  # Extract input PDF file name without extension
    splitted_pdf_paths = []
    
    with open(config.input_file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)
       
        pdf_file_folder = os.path.join(config.output_file_path, f"{input_pdf_name}/extracted_pdfs")
         # Create the output folder if it doesn't exist
        os.makedirs(pdf_file_folder, exist_ok=True)
        
        for page_number in range(total_pages):
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_number])
            
            output_pdf = f"{pdf_file_folder}/{input_pdf_name}_page_{page_number + 1}.pdf"
            splitted_pdf_paths.append(output_pdf)
            
            with open(output_pdf, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            #print(f"Page {page_number + 1} saved as {output_pdf}")
            log.info(f"Page {page_number + 1} saved as {output_pdf}")
    
    return splitted_pdf_paths

    #return split(config.input_file_path, config.output_file_path)

@asset
def pdf_to_png_image(split_pdf):
    """
    Function to convert PDF page files to PNG image files. Uses pdf2image library
    The argument 'split_pdf' takes the output from the 'split_pdf' function as input, following Dagster's naming convention.
    

    Args:
    - split_pdf: List of paths to the individual PDF page files.

    Returns:
    - List of paths to the generated PNG image files.
    """

    extracted_image_files = []

    for idx, pdf_path in enumerate(split_pdf):
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            # Save the image 
            image_name = os.path.splitext(os.path.basename(pdf_path))[0]
           
            image_file_name = f"{image_name}.png"
           
            image_file_folder = os.path.dirname(pdf_path).replace("extracted_pdfs","extracted_images")
           
            # Create the folder if it doesn't exist
            os.makedirs(image_file_folder, exist_ok=True)
            
            # Construct the full path for the image file
            image_file_path = image_file_folder + "/" +  image_file_name
            
            # Save the image as PNG
            image.save(image_file_path, format="PNG") 
            
            # Construct the full path for the image file
            image_file_path = os.path.join(image_file_folder, image_file_name)
            
            # Append the path of the extracted image file to the list
            extracted_image_files.append(image_file_path)
            
    return extracted_image_files

@asset
def extract_text_from_png(pdf_to_png_image,config: AssetCongigs):
    """
    Function to extract text from PNG images using OCR. Uses pytesseract to perform OCR on PNG images to extract text.
    The argument 'pdf_to_png_image' takes the output from the 'pdf_to_png_image' function as input.
    

    Args:
    - pdf_to_png_image: List of paths to the PNG image files.
    - config: AssetConfigs object containing configurations for the asset.

    Returns:
    - List of paths to the text files containing the extracted text.
    """

    extracted_text_files = []

    for idx, png_path in enumerate(pdf_to_png_image):
        # Load the image from the path
        image = Image.open(png_path)
        
        # Perform OCR on the image and extract text
        text = pytesseract.image_to_string(image, lang=config.ocr_lang if config.ocr_lang else 'eng')
        # Get the image name without extension
        text_file_name = os.path.splitext(os.path.basename(png_path))[0]
        
        # Create a unique text file name based on the image name, PDF page index, and image index
        text_file_name = f"{text_file_name}.txt"
        text_file_folder = os.path.join(os.path.dirname(png_path).replace("extracted_images", ""), "extracted_text")
        
        # Create the folder if it doesn't exist
        os.makedirs(text_file_folder, exist_ok=True)

        # Construct the full path for the text file
        text_file_path = text_file_folder + "/" + text_file_name
    

        with open(text_file_path, 'w') as text_file:
            text_file.write(text)
        
        # Append the path of the extracted text file to the list
        extracted_text_files.append(text_file_path)

    return extracted_text_files
    
    
@asset
def build_json_documents(extract_text_from_png):
    """
    Function to build JSON documents from the text extracted from PNG images.
    Constructs JSON documents with the extracted text and metadata from PNG images.
    The argument 'extract_text_from_png' takes the output from the 'extract_text_from_png' function as input.
    
    Args:
    - extract_text_from_png: List of paths to the text files with extracted text.

    Returns:
    - List of JSON objects representing the documents.
    """
    
   # Initialize an array to store the JSON book documents
    book_documents = []
    book_title = os.path.basename(extract_text_from_png[0]).split('_')[0]
    for idx, file_path in enumerate(extract_text_from_png):
            # Read the text from the file
            with open(file_path, "r") as file:
                text = file.read()


            # Create a book document as a dictionary
            book_document = {
                "title": book_title,
                "author": "John Smith",
                "publication_date": "2023-08-20",
                "isbn": "978-1234567890",
                "language": "English",
                "genre": ["Adventure"],
                "content": text,
                "content_as_image":file_path
            }
           
             # Append the book document to the array
            book_documents.append(book_document)
       

    return book_documents

@asset
def save_to_disk(build_json_documents):
    """
    Function to save JSON documents to disk.
    The argument 'build_json_documents' takes the output from the 'build_json_documents' function as input.
    
    Args:
    - build_json_documents: List of JSON objects representing the documents.

    Returns:
    - List of JSON objects that were saved to disk.
    """

    json_string = json.dumps(build_json_documents, indent=4, ensure_ascii=False)
    # Save the book documents as a JSON file
    output_file_path = build_json_documents[0]["title"] + ".json"
    with open(output_file_path, "w",encoding="utf-8") as json_file:
            json_file.write(json_string)
    return build_json_documents


@asset
def save_to_elasticsearch(save_to_disk):
    """
    Function to index JSON documents in Elasticsearch (cloud)
    The argument 'save_to_disk' takes the output from the 'save_to_disk' function as input.
    
    Args:
    - save_to_disk: List of JSON objects representing the documents.

    Returns:
    - None
    """
    cloud_id = f"${ES_INDEX_NAME}:${ES_CLOUD_ID}"  
    cloud_auth = (ES_CLOUD_USERNAME, ES_CLOUD_PASSWORD)  # Replace with your Cloud username and password
    es = Elasticsearch( cloud_id=cloud_id, http_auth=cloud_auth )
    index_name = ES_INDEX_NAME

    for ebook in save_to_disk:
        # Index each eBook document
        es.index(index=index_name, body=ebook)

    # Refresh the index
    es.indices.refresh(index=index_name)

    
    return None



