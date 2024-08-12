from bs4 import BeautifulSoup
import requests

def get_headlines(url: str) -> list[str]:
    """Fetch and return headlines from the given URL."""
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = [h3.text for h3 in soup.find_all('h3')]  # Assuming headlines are inside <h3> tags
    return headlines
