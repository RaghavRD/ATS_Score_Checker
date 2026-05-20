import urllib.request
import urllib.parse
import json
import ssl

def test_api():
    base_url = "https://linkedin-job-search-api.p.rapidapi.com/active-jb-24h"
    
    # Query parameters
    params = {
        "limit": "5",
        "offset": "0",
        "title_filter": "Python developer",
        "location_filter": "India",
        "description_type": "text"
    }
    
    # Construct URL
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"
    
    # Headers
    headers = {
        "x-rapidapi-host": "linkedin-job-search-api.p.rapidapi.com",
        "x-rapidapi-key": "832bae4e1cmshba851e21a8e0a0cp1106cejsnb8fdebe31e7d"  # Key provided by user
    }
    
    print(f"Testing API URL: {url}")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        # Create unverified context to avoid SSL errors in some environments
        context = ssl._create_unverified_context()
        
        with urllib.request.urlopen(req, context=context) as response:
            status_code = response.getcode()
            print(f"Status Code: {status_code}")
            
            data = response.read()
            json_data = json.loads(data)
            
            print("\nResponse Data Sample (First 2 jobs):")
            print(json.dumps(json_data[:2] if isinstance(json_data, list) else json_data, indent=2))
            
            print("\nKeys in response:", json_data[0].keys() if isinstance(json_data, list) and json_data else "No list returned")
            
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
