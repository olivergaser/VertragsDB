import requests
import io

BASE_URL = "http://localhost:8000"

def test_upload_and_download():
    # 1. Create contract with file
    file_content = b"This is a test PDF content."
    files = {'file': ('test.pdf', file_content, 'application/pdf')}
    data = {
        "partner": "Test Partner",
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "notice_period": "3 months",
        "amount": "100.0",
        "category": "Sonstiges"
    }
    
    print("Creating contract...")
    res = requests.post(f"{BASE_URL}/contracts/", data=data, files=files)
    if res.status_code != 200:
        print(f"Failed to create contract: {res.text}")
        return
    
    contract = res.json()
    contract_id = contract['id']
    print(f"Contract created with ID: {contract_id}")
    print(f"Document path: {contract.get('document_path')}")
    
    if not contract.get('document_path'):
        print("Error: Document path not set!")
        return

    # 2. Download document
    print("Downloading document...")
    res_doc = requests.get(f"{BASE_URL}/contracts/{contract_id}/document")
    if res_doc.status_code == 200:
        downloaded_content = res_doc.content
        if downloaded_content == file_content:
            print("SUCCESS: Downloaded content matches uploaded content!")
        else:
            print("FAILURE: Content mismatch!")
            print(f"Expected: {file_content}")
            print(f"Got: {downloaded_content}")
    else:
        print(f"Failed to download document: {res_doc.status_code} {res_doc.text}")

    # 3. Clean up (optional, but good practice)
    # requests.delete(f"{BASE_URL}/contracts/{contract_id}")

if __name__ == "__main__":
    test_upload_and_download()
