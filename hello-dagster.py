
from dagster import AssetIn, asset, Config
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
import os
from pdf2image import convert_from_path
from PIL import Image

class AssetCongigs(Config):
    input_file_path: str
    output_file_path: str

@asset
def split_pdf(context,config: AssetCongigs):
    # Implement the logic to split the PDF into individual pages
    # Return a list of paths to the splitted PDF pages
    return split(config.input_file_path, config.output_file_path)

@asset
def pdf_to_png_image(split_pdf):
   
    extracted_image_files = []

    for idx, pdf_path in enumerate(split_pdf):
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            # Save the image
            image_name = os.path.dirname(pdf_path).split('/')[-1]
            image_file_name = f"{image_name}_page_{idx + 1}.png"
            image_file_folder = os.path.join(os.path.dirname(pdf_path), "extracted_images")
            
            # Create the folder if it doesn't exist
            os.makedirs(image_file_folder, exist_ok=True)
            
            # Construct the full path for the image file
            image_file_path = os.path.join(image_file_folder, image_file_name)
            
            # Save the image as PNG
            image.save(image_file_path, format="PNG") 
            
            # Construct the full path for the image file
            image_file_path = os.path.join(image_file_folder, image_file_name)
            
            # Append the path of the extracted image file to the list
            extracted_image_files.append(image_file_path)
            
    return extracted_image_files

@asset
def extract_text_from_png(pdf_to_png_image):
    extracted_text_files = []

    for idx, png_path in enumerate(pdf_to_png_image):
        # Load the image from the path
        image = Image.open(png_path)
        
        # Perform OCR on the image and extract text
        text = pytesseract.image_to_string(image, lang='tam')
        
        # Get the image name without extension
        image_name = os.path.basename(png_path).split('.')[0]
        
        # Create a unique text file name based on the image name, PDF page index, and image index
        text_file_name = f"{image_name}_page_{idx + 1}.txt"
        text_file_folder = os.path.join(os.path.dirname(png_path).replace("extracted_images", ""), "extracted_text")
        
        # Create the folder if it doesn't exist
        os.makedirs(text_file_folder, exist_ok=True)

        # Construct the full path for the text file
        text_file_path = os.path.join(text_file_folder, text_file_name)

        with open(text_file_path, 'w') as text_file:
            text_file.write(text)
        
        # Append the path of the extracted text file to the list
        extracted_text_files.append(text_file_path)
    
    return None




def split(input_pdf, output_folder):
    input_pdf_name = input_pdf.split('/')[-1].split('.')[0]  # Extract input PDF file name without extension
    splitted_pdf_paths = []
    
    with open(input_pdf, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)

         # Create the output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        for page_number in range(total_pages):
            pdf_writer = PyPDF2.PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[page_number])
            
            output_pdf = f"{output_folder}/{input_pdf_name}_page_{page_number + 1}.pdf"
            splitted_pdf_paths.append(output_pdf)
            
            with open(output_pdf, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            print(f"Page {page_number + 1} saved as {output_pdf}")
    
    return splitted_pdf_paths

