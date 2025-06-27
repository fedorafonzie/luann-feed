import requests
import json
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

print("Script gestart: Ophalen van de dagelijkse Luann strip.")

# URL van de Luann comic pagina
LUANN_URL = 'https://www.gocomics.com/luann'

# Stap 1: Haal de webpagina op
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    response = requests.get(LUANN_URL, headers=headers)
    response.raise_for_status()
    print("SUCCES: GoComics pagina HTML opgehaald.")
except requests.exceptions.RequestException as e:
    print(f"FOUT: Kon GoComics pagina niet ophalen. Fout: {e}")
    exit(1)

# --- DEFINITIEVE METHODE V3: Filteren van 'favorieten' ---
print("Zoeken naar de correcte JSON-LD script tag en filteren van favorieten...")

image_url = None
try:
    soup = BeautifulSoup(response.text, 'lxml')

    # Vind ALLE script tags van het type 'application/ld+json'
    all_json_ld_scripts = soup.find_all('script', type='application/ld+json')

    if not all_json_ld_scripts:
        raise ValueError("Geen 'application/ld+json' script tags gevonden op de pagina.")

    for script in all_json_ld_scripts:
        if script.string:
            try:
                data = json.loads(script.string)

                # Controleer of dit een valide 'ImageObject' is dat de pagina representeert
                if (isinstance(data, dict) and
                        data.get('@type') == 'ImageObject' and
                        data.get('representativeOfPage') is True and
                        'url' in data):
                    
                    # --- DE CRUCIALE EXTRA CONTROLE ---
                    # Zoek "omhoog" vanaf het script om te zien of het in de 'FiveFavorites' sectie zit.
                    if script.find_parent('section', class_='ShowFiveFavorites_showFiveFavorites__zsqHu'):
                        # Ja, dit is een favoriet. Negeer deze en ga door naar de volgende in de loop.
                        print(f"INFO: 'Favoriet' afbeelding genegeerd: ...{data['url'][-20:]}")
                        continue
                    
                    # Als de code hier komt, is het GEEN favoriet. Dit is de hoofdafbeelding.
                    image_url = data['url']
                    print(f"SUCCES: Hoofdafbeelding gevonden: {image_url}")
                    break  # Stop de loop, we zijn klaar.

            except (json.JSONDecodeError, AttributeError):
                continue
    
    if not image_url:
        raise ValueError("Kon de hoofdafbeelding niet isoleren van de favorieten.")

except (ValueError, KeyError, TypeError) as e:
    print(f"FOUT: Kon de URL niet uit de data halen. Het script is mogelijk verouderd.")
    print(f"Foutdetails: {e}")
    with open("debug_gocomics.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("De ontvangen HTML is opgeslagen in 'debug_gocomics.html' voor analyse.")
    exit(1)
# --- EINDE DEFINITIEVE METHODE ---
    
# De rest van het script blijft ongewijzigd
# ... (Stap 3 & 4) ...
fg = FeedGenerator()
fg.id(LUANN_URL)
fg.title('Luann Comic Strip')
fg.link(href=LUANN_URL, rel='alternate')
fg.description('De dagelijkse Luann strip.')
fg.language('en')

current_date = datetime.now(timezone.utc)
current_date_str = current_date.strftime("%Y-%m-%d")

fe = fg.add_entry()
fe.id(image_url)
fe.title(f'Luann - {current_date_str}')
fe.link(href=LUANN_URL)
fe.pubDate(current_date)
fe.description(f'<img src="{image_url}" alt="Luann Strip voor {current_date_str}" />')

try:
    fg.rss_file('luann.xml', pretty=True)
    print("SUCCES: 'luann.xml' is aangemaakt met de strip van vandaag.")
except Exception as e:
    print(f"FOUT: Kon het bestand niet wegschrijven. Foutmelding: {e}")
    exit(1)