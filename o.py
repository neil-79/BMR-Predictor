import requests

# Endpoint URL with a query parameter for the song "Khoobsurat" from "Street 2"
url = 'http://127.0.0.1:5000/song/?query=https://www.jiosaavn.com/song/khoobsurat-from-street-2&lyrics=true'

# Make a GET request to the API
response = requests.get(url)

# Print the response content (JSON), which includes lyrics if available
print(response.json())
