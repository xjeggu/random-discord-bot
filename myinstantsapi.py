import requests
from bs4 import BeautifulSoup
import json

def remove_duplicates(data):
    if isinstance(data, list):
        unique_items = list({tuple(sorted(d.items())): d for d in data}.values())
    elif isinstance(data, dict):
        unique_items = {tuple(sorted(data.items())): data}
    else:
        unique_items = tuple(set(data))
    
    return unique_items

# request myinstants
def get_sound_url(name,max_url_length):
  r = requests.get(f'http://www.myinstants.com/search/?name={name}')
  soup = BeautifulSoup(r.text, 'html.parser')
  buttonList = []

  # each button
  for link in soup.find_all("div", class_="instant"):
    # name
    buttonName = link.a.text
    # parse song url
    buttonUrl = link.find("button", class_="small-button")
    s = buttonUrl['onclick']
    buttonUrl = s.partition("('")[-1].rpartition("')")[0]
    # button obj
    fullUrl = 'https://www.myinstants.com' + buttonUrl
    if len(fullUrl) <= max_url_length:
      button = {
          "name": buttonName,
          "url": fullUrl
      }
      buttonList.append(button)

  return json.dumps(remove_duplicates(buttonList))

    # show
    #return("https://www.myinstants.com" + json.dumps(buttonList[0]["url"].split(",")[0]))

