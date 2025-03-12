# XML to Excel Converter

This is a simple Flask application that converts XML files into Excel files.

## Features

- Upload an XML file via a web interface.
- Converts the XML to JSON and processes it using custom conversion functions.
- Generates an Excel file (`output.xlsx`) from the extracted data.

## Requirements

Install the dependencies using:

```sh
pip install -r Requirements.txt
```

## Running the Application

Start the application with:

```sh
python app.py
```

The server will run in debug mode at [http://localhost:5000](http://localhost:5000).

## File Structure

- **app.py**: The main Flask application file.
- **Input.xml**: A sample XML file.
- **Requirements.txt**: The list of dependencies.
- **templates/upload.html**: HTML template for uploading XML files.

## Notes

Make sure the functions `convert_xml_to_json(xml_data)` and `extract_json(json_data)` are defined in your project to handle the conversion logic.