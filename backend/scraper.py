from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import json

chrome_options = Options()
chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

URL = "https://gamevlg.com/pokemon-tcg-pocket/cards"
driver.get(URL)

time.sleep(5)

try: 
    with open("pokemon_cards.json", "r", encoding="utf-8") as json_file:
        all_cards = json.load(json_file)
        existing_cards = {(card["name"], card["image_url"]) for card in all_cards}
except (FileNotFoundError, json.JSONDecodeError):
    all_cards = []
    existing_cards = set()

card_elements = [img for img in driver.find_elements(By.TAG_NAME, "img") if "Logo" not in img.get_attribute("alt")]

print(f"Found {len(card_elements)} cards on page.")
i = 0
while i <len(card_elements):
    try:
        card_elements = [img for img in driver.find_elements(By.TAG_NAME, "img") if "Logo" not in img.get_attribute("alt")]
        if i >= len(card_elements):
            print("All cards scraped!")
            break

        card = card_elements[i]
        card_name = card.get_attribute("alt")
        card_image_url = card.get_attribute("src")

        if (card_name, card_image_url) in existing_cards:
            print(f"Skipping duplicate: {card_name}")
            i+=1
            continue

        print(f"Clicking on {card_name}...")

        card.click()

        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Print all table rows for debugging
        print("🟡 DEBUG: Extracting details for", card_name)

        card_type = "Unknown Type"
        card_rarity = "Unknown Rarity"
        card_set = "Unknown Set"

        all_rows = soup.find_all("tr")
        for row in all_rows:
            columns = row.find_all("td")
            if len(columns) == 2:
                label = columns[0].text.strip()
                value_td = columns[1]
                value = value_td.text.strip() if value_td.text.strip() else "Unknown"

                if "Type" in label:
                    card_type = value

                elif "Rarity" in label:
                    rarity_img = value_td.find("img")
                    if rarity_img:
                        card_rarity = rarity_img["alt"].strip()
                    else:
                        card_rarity = "No Rarity Listed"
            
                elif "Set" in label:
                    set_link = value_td.find("a")
                    card_set = set_link.text.strip() if set_link else value
        
        card_data = {
            "name":card_name,
            "set_name":card_set,
            "type": card_type,
            "rarity":card_rarity,
            "image_url":card_image_url,
        }
        all_cards.append(card_data)
        existing_cards.add((card_name, card_image_url))

        # # 🟢 Extract Type (Looks inside <td> -> <a>)
        # type_element = soup.find("td", string=lambda text: text and "Type" in text)
        # if type_element:
        #     type_link = type_element.find_next("a")
        #     card_type = type_link.text.strip() if type_link else type_element.find_next("td").text.strip()

        # # 🟢 Extract Rarity (Plain text inside second column)
        # rarity_element = soup.find("td", string=lambda text: text and "Rarity" in text)
        # if rarity_element:
        #     card_rarity = rarity_element.find_next("td").text.strip()

        # # 🟢 Extract Set Name (Find <a> inside <td>)
        # set_element = soup.find("td", string=lambda text: text and "Set" in text)
        # if set_element:
        #     set_link = set_element.find("a")  # Look for an <a> tag
        #     card_set = set_link.text.strip() if set_link else set_element.find_next("td").text.strip()


        # type_element = soup.find("td", string=lambda text: text and "Type" in text)
        # card_type = type_element.find_next("a").text.strip() if type_element else "Unknown Type"

        # rarity_element = soup.find("td",string ="Rarity")
        # card_rarity = rarity_element.find_next_sibling("td").text.strip() if rarity_element else "Unknown Rarity"


        # set_element = soup.find("td",string= lambda text: text and "Set" in text)
        # card_set = set_element.find_next("a").text.strip() if set_element and set_element.find("a") else "Unknown Set"


        # print(f"Card Name: {card_name}")
        # print(f"Set Name: {card_set}")
        # print(f"Type: {card_type}")
        # print(f"Rarity: {card_rarity}")
        # print(f"Image URL: {card_image_url}")
        print(f"Successfully scraped: {card_name}")
        print("-" * 40)

        driver.back()
        time.sleep(3)
        # card_elements = driver.find_elements(By.TAG_NAME, "img")
        i += 1
    except Exception as e:
        print (f"Error scraping {card_name}: {e}")
        driver.back()
        time.sleep(3)
        i+=1

with open("pokemon_cards.json", "w", encoding="utf-8") as json_file:
    json.dump(all_cards, json_file, indent=4, ensure_ascii=False)
    
print("Succesfully saved scraped data to 'pokemon_cards.json'!")
driver.quit()