# dagster-data-flows
Explore captivating data pipelines and workflow solutions using Dagster. This repository showcases a collection of diverse and engaging use cases, demonstrating the power and versatility of Dagster in managing, orchestrating, and optimizing data flows. Join us on this journey of discovery and innovation in data engineering and workflow automation.


## Python Environment Setup and activation



```bash
python3 -m venv env
```

```bash
source env/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

## Run the pipeline

```bash
dagster dev -f ./zybot-text-extract-from-pdf.py 
```


##
Input variable

```python
{
  'ops': {
    'split_pdf': {
      'config': {
        'input_file_path': '/Users/skaruppaiah1/projects/dagster-data-flows/input/mogni-theevu.pdf',
        'output_file_path': '/Users/skaruppaiah1/projects/dagster-data-flows/output',
        'ocr_lang': 'tam'
      }
    },
    'extract_text_from_png': {
      'config': {
        'input_file_path': '/input/mogni-theevu.pdf',
        'output_file_path': '/output',
        'ocr_lang': 'tam'
      }
    }
  }
}
```
> Note: Please change the input_file_path and output_file_path accordingly. The output file path should be a directory and not a file path. The output file will be named as the input file name with the page number appended to it. For example, if the input file name is `Ilaiya-Raani.pdf`, the output file will be named as `Ilaiya-Raani_1.pdf` for the first page, `Ilaiya-Raani_2.pdf` for the second page and so on.