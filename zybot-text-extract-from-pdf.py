
import json
from dagster import AssetIn, asset, Config
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
import os
from pdf2image import convert_from_path
from PIL import Image
from elasticsearch import Elasticsearch

class AssetCongigs(Config):
    input_file_path: str
    output_file_path: str
    ocr_lang: str

@asset
def split_pdf(context,config: AssetCongigs):
    # Implement the logic to split the PDF into individual pages
    # Return a list of paths to the splitted PDF pages

    input_pdf_name = config.input_file_path.split('/')[-1].split('.')[0]  # Extract input PDF file name without extension
    splitted_pdf_paths = []
    
    with open(config.input_file_path, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)

        # Create the output folder if it doesn't exist
        os.makedirs(config.output_file_path, exist_ok=True)
        
        for page_number in range(total_pages):
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_number])
            
            output_pdf = f"{config.output_file_path}/{input_pdf_name}_page_{page_number + 1}.pdf"
            splitted_pdf_paths.append(output_pdf)
            
            with open(output_pdf, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            print(f"Page {page_number + 1} saved as {output_pdf}")
    
    return splitted_pdf_paths

    #return split(config.input_file_path, config.output_file_path)

@asset
def pdf_to_png_image(split_pdf):
   
    extracted_image_files = []

    for idx, pdf_path in enumerate(split_pdf):
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            # Save the image 
            image_name = os.path.splitext(os.path.basename(pdf_path))[0]
            print("pdf_path=",pdf_path)
            image_file_name = f"{image_name}.png"
            print("image_file_name=",image_file_name)
            image_file_folder = os.path.join(os.path.dirname(pdf_path), "extracted_images")
            print("image_file_folder=",image_file_folder)
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
    json_string = json.dumps(build_json_documents, indent=4, ensure_ascii=False)
    # Save the book documents as a JSON file
    output_file_path = build_json_documents[0]["title"] + ".json"
    with open(output_file_path, "w",encoding="utf-8") as json_file:
            json_file.write(json_string)
    return build_json_documents



    
@asset
def save_to_elasticsearch(save_to_disk):
    cloud_id = 'ebooks:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyRlOTdhNGI0NzBlMmE0OWNmYjBlMTBjOWJiMzQ2NTQxNSQ4OTQ5NjU2OTU3ZGM0MzUwOTYwYWU5ODcyZjEzMTVlZg=='  # Replace with your Elastic Cloud ID
    cloud_auth = ('elastic', 'n26ugDzFh4NhGldmQDKMyKm0')  # Replace with your Cloud username and password
    es = Elasticsearch( cloud_id=cloud_id, http_auth=cloud_auth )
    index_name = 'ebooks'

    for ebook in save_to_disk:
        # Index each eBook document
        es.index(index=index_name, body=ebook)

    # Refresh the index
    es.indices.refresh(index=index_name)

    
    return None



