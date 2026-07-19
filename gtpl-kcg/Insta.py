import requests

# Function to download image files:
def downloadFile(url, name):
    print(f"Started Downloading {name}")
    response = requests.get(url)
    open(f"{name}.html", "wb").write(response.content)
    print(f"Finished Downloading {name}")

url = "https://www.instagram.com/p/CzPMVCJKMKc/?igsh=MW4wZmV4ajducnl1cQ==" # URL to download random images with resolution 2000x3000

downloadFile(url, "insta")

