import xml.etree.ElementTree as ET
import json
import argparse
import pandas as pd
from flask import Flask, request, render_template, send_file
import xmltodict
import os

def xml_to_dict(element):
    node = {}

    if element.attrib:
        node["@attributes"] = element.attrib
    
    children = list(element)
    if children:
        child_dict = {}
        for child in children:
            child_data = xml_to_dict(child)
            child_tag = list(child_data.keys())[0]
            child_value = child_data[child_tag]
            if child_tag in child_dict:
                
                if not isinstance(child_dict[child_tag], list):
                    child_dict[child_tag] = [child_dict[child_tag]]
                child_dict[child_tag].append(child_value)
            else:
                child_dict[child_tag] = child_value
        node.update(child_dict)

    
    text = element.text.strip() if element.text is not None else ""
    if text:
        if node:
            node["#text"] = text
        else:
            node = text

    return {element.tag: node}

def convert_xml_to_json(xml_string):

    root = ET.fromstring(xml_string)
    dict_data = xml_to_dict(root)
    return json.dumps(dict_data, indent=4)



    
def extract_json(json_data):
    
    json_data = json.loads(json_data)
    final_result = []
    
    datarow_template = {
        "Date": "",
        "Transaction Type": "",
        "Vch No.": "",
        "Ref No": "",
        "Ref Type": "",
        "Ref Date": "",
        "Debtor": "",
        "Ref Amount": "",
        "Amount": "",
        "Particulars": "",
        "Vch Type": "",
        "Amount Verified": "",
    }
    

    
    Tally_Messages = json_data["ENVELOPE"]["BODY"]["IMPORTDATA"]["REQUESTDATA"]["TALLYMESSAGE"]

    
    for Tally_Message in Tally_Messages:
        if Tally_Message["VOUCHER"]["@attributes"]["VCHTYPE"] == "Receipt":
            Date = Tally_Message["VOUCHER"]["DATE"]
            Date = f"{Date[6:8]}-{Date[4:6]}-{Date[0:4]}"
            VchType = Tally_Message["VOUCHER"]["@attributes"]["VCHTYPE"]
            VoucherNumber = Tally_Message["VOUCHER"]["VOUCHERNUMBER"]
            ParentParticular = Tally_Message["VOUCHER"]["ALLLEDGERENTRIES.LIST"][0]["LEDGERNAME"]
            OtherParticular = Tally_Message["VOUCHER"]["ALLLEDGERENTRIES.LIST"][1]["LEDGERNAME"]
            ParentAmount = Tally_Message["VOUCHER"]["ALLLEDGERENTRIES.LIST"][0]["AMOUNT"]
            OtherAmount = Tally_Message["VOUCHER"]["ALLLEDGERENTRIES.LIST"][1]["AMOUNT"]
            
            billAllocations = Tally_Message["VOUCHER"]["ALLLEDGERENTRIES.LIST"][0]["BILLALLOCATIONS.LIST"]
        
            
            child_records = []
            childTotalAmount = 0.0
            
            if billAllocations:
                if isinstance(billAllocations, dict):
                    billAllocations = [billAllocations]

                for bill in billAllocations:
                    if isinstance(bill, dict):
                        RefNo = bill["NAME"]
                        RefType = bill["BILLTYPE"]
                        RefAmount = bill["AMOUNT"]
                        
                        child_record = {}
                        for key in datarow_template:
                            child_record[key] = datarow_template[key]
                            
                        child_record["Date"] = Date
                        child_record["Transaction Type"] = "Child"
                        child_record["Vch No."] = VoucherNumber
                        child_record["Ref No"] = RefNo
                        child_record["Ref Type"] = RefType
                        child_record["Debtor"] = ParentParticular
                        child_record["Ref Amount"] = RefAmount
                        child_record["Amount"] = "NA"
                        child_record["Particulars"] = ParentParticular
                        child_record["Vch Type"] = VchType
                        child_record["Amount Verified"] = "NA"
                        
                        childTotalAmount += float(RefAmount)
                        child_records.append(child_record)
            
            parent_record = {}
            for key in datarow_template:
                parent_record[key] = datarow_template[key]
                
            parent_record["Date"] = Date
            parent_record["Transaction Type"] = "Parent"
            parent_record["Vch No."] = VoucherNumber
            parent_record["Ref No"] = "NA"
            parent_record["Ref Type"] = "NA"
            parent_record["Ref Date"] = "NA"
            parent_record["Debtor"] = ParentParticular
            parent_record["Ref Amount"] = "NA"
            parent_record["Amount"] = ParentAmount
            parent_record["Particulars"] = ParentParticular
            parent_record["Vch Type"] = VchType
            
            
            parent_record["Amount Verified"] = "Yes" if float(ParentAmount) ==  childTotalAmount else "No"
            
            
            other_record = {}
            for key in datarow_template:
                other_record[key] = datarow_template[key]
                
            other_record["Date"] = Date
            other_record["Transaction Type"] = "Other"
            other_record["Vch No."] = VoucherNumber
            other_record["Ref No"] = "NA"
            other_record["Ref Type"] = "NA"
            other_record["Ref Date"] = "NA"
            other_record["Debtor"] = OtherParticular
            other_record["Ref Amount"] = "NA"
            other_record["Amount"] = OtherAmount
            other_record["Particulars"] = OtherParticular
            other_record["Vch Type"] = VchType
            other_record["Amount Verified"] = "NA"
            
            
            final_result.append(parent_record)
            final_result.extend(child_records)
            final_result.append(other_record)
        
    
    
    if not final_result:
        print("Warning: No data extracted. Returning empty DataFrame.")
        return pd.DataFrame(columns=datarow_template.keys())
    
    try:
        df = pd.DataFrame(final_result)
    except Exception as e:
        print(f"Error creating DataFrame: {e}")
    
    try:
        output_excel_file = "output.xlsx"
        df.to_excel(output_excel_file, index=False)
        print(f"Result has been written to {output_excel_file}")
    except Exception as e:
        print(f"Error writing to Excel: {e}")
    
    return df




app = Flask(__name__)

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/convert', methods=['POST'])
def convert_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        xml_data = file.read().decode('utf-8')
        json_data = convert_xml_to_json(xml_data)
        df = extract_json(json_data)
        output_excel_file = "output.xlsx"
        df.to_excel(output_excel_file, index=False)
        return send_file(output_excel_file, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)