import requests
import pandas as pd
from bs4 import BeautifulSoup

url = "https://finance.naver.com/sise/sise_market_sum.naver?sosok=0"
post_url = "https://finance.naver.com/sise/field_submit.nhn"

session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Step 1: Send a get to establish session cookies
session.get(url, headers=headers)

# Step 2: Post the fields we want to check
payload = {
    "menu": "market_sum",
    "fieldIds": ["market_sum", "per", "pbr", "roe", "dividend", "quant"],
    "returnUrl": url
}

r = session.post(post_url, headers=headers, data=payload)

# Step 3: Get the page
r_get = session.get(url + "&page=1", headers=headers)

# Step 4: Parse using pandas
dfs = pd.read_html(r_get.text)
print("Number of tables:", len(dfs))
for idx, df in enumerate(dfs):
    print(f"Table {idx} columns:", df.columns)
    print(df.dropna(how='all').head(10))
