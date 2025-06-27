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

# --- DEFINITIEVE METHODE V2: Zoek naar de JUISTE JSON-LD tag op basis van inhoud ---
print("Zoeken naar de correcte JSON-LD script tag op de pagina...")

image_url = None
try:
    soup = BeautifulSoup(response.text, 'lxml')

    # 1. Vind ALLE script tags van het type 'application/ld+json'
    all_json_ld_scripts = soup.find_all('script', type='application/ld+json')

    if not all_json_ld_scripts:
        raise ValueError("Geen 'application/ld+json' script tags gevonden op de pagina.")

    # 2. Loop door elke gevonden script tag om de juiste te vinden
    for script in all_json_ld_scripts:
        # Zorg ervoor dat de tag inhoud heeft om fouten te voorkomen
        if script.string:
            try:
                # 3. Laad de inhoud als JSON
                data = json.loads(script.string)

                # 4. Controleer of dit de JUISTE JSON-blob is.
                # We zoeken naar een 'ImageObject' dat de pagina representeert ('representativeOfPage').
                if (isinstance(data, dict) and
                        data.get('@type') == 'ImageObject' and
                        data.get('representativeOfPage') is True and
                        'url' in data):
                    
                    # Gevonden! Pak de URL en stop met zoeken.
                    image_url = data['url']
                    print(f"SUCCES: Correcte JSON-LD data gevonden. URL: {image_url}")
                    break  # Verlaat de for-loop, we hebben wat we nodig hebben

            except (json.JSONDecodeError, AttributeError):
                # Soms is een script tag leeg of incorrect, negeer en ga door naar de volgende.
                continue
    
    # Als na de loop geen URL is gevonden, geef dan een fout.
    if not image_url:
        raise ValueError("Kon de specifieke JSON-LD met de comic URL niet vinden tussen alle script tags.")

except (ValueError, KeyError, TypeError) as e:
    print(f"FOUT: Kon de URL niet uit de data halen. Het script is mogelijk verouderd.")
    print(f"Foutdetails: {e}")
    with open("debug_gocomics.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    print("De ontvangen HTML is opgeslagen in 'debug_gocomics.html' voor analyse.")
    exit(1)
# --- EINDE DEFINITIEVE METHODE ---
    
# Stap 3: Bouw de RSS-feed (ongewijzigd)
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

# Stap 4: Schrijf het XML-bestand weg (ongewijzigd)
try:
    fg.rss_file('luann.xml', pretty=True)
    print("SUCCES: 'luann.xml' is aangemaakt met de strip van vandaag.")
except Exception as e:
    print(f"FOUT: Kon het bestand niet wegschrijven. Foutmelding: {e}")
    exit(1)