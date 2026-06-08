import time
import json
import pandas as pd

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager

def start_driver():

    options = webdriver.ChromeOptions()

    # supaya ringan
    # options.add_argument("--headless")

    # anti bot ringan
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    return driver

def scrape_recipe_links(driver, query="masakan indonesia"):

    query = query.replace(" ", "%20")

    url = f"https://cookpad.com/id/cari/{query}?order=latest"

    driver.get(url)

    time.sleep(1)

    # ======================
    # AUTO SCROLL
    # ======================

    for i in range(5):

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

        print(f"Scroll ke-{i+1}")

        time.sleep(3)

    # ======================
    # PARSING HTML
    # ======================

    soup = BeautifulSoup(
        driver.page_source,
        "html.parser"
    )

    recipe_links = []

    seen = set()

    links = soup.select(
        'a[href*="/resep/"], a[href*="/recipe/"]'
    )

    print("Total raw links:", len(links))

    for a in links:

        href = a.get("href")

        if not href:
            continue

        # normalize URL
        if href.startswith("http"):
            full_link = href
        else:
            full_link = "https://cookpad.com" + href

        # ======================
        # FILTER LINK INVALID
        # ======================

        # skip halaman kategori
        if "/resep/baru" in full_link:
            continue

        # hanya ambil resep numerik
        # contoh:
        # /resep/25806302
        if not full_link.split("/")[-1].isdigit():
            continue

        # anti duplicate
        if full_link in seen:
            continue

        seen.add(full_link)

        recipe_links.append(full_link)

    print("Total unique recipes:", len(recipe_links))

    return recipe_links

def get_recipe_detail(driver, url):

    driver.get(url)

    time.sleep(5)

    soup = BeautifulSoup(
        driver.page_source,
        "html.parser"
    )

    # ======================
    # DEFAULT VALUE
    # ======================

    title = "Unknown"
    ingredients = []
    steps = []
    author = "Unknown"
    servings = "Unknown"

    # ======================
    # AMBIL JSON-LD
    # ======================

    scripts = soup.find_all(
        "script",
        type="application/ld+json"
    )

    for script in scripts:

        try:

            if not script.string:
                continue

            data = json.loads(script.string)

            # kadang bentuknya list
            if isinstance(data, list):

                for item in data:

                    if (
                        isinstance(item, dict)
                        and item.get("@type") == "Recipe"
                    ):

                        data = item
                        break

            # ======================
            # JIKA RECIPE
            # ======================

            if (
                isinstance(data, dict)
                and data.get("@type") == "Recipe"
            ):

                # TITLE
                title = data.get(
                    "name",
                    "Unknown"
                )

                # INGREDIENTS
                ingredients = data.get(
                    "recipeIngredient",
                    []
                )

                # STEPS
                instructions = data.get(
                    "recipeInstructions",
                    []
                )

                for step in instructions:

                    if isinstance(step, dict):

                        text = step.get("text")

                        if text:
                            steps.append(text)

                    elif isinstance(step, str):

                        steps.append(step)

                # AUTHOR
                author_data = data.get("author")

                if isinstance(author_data, dict):

                    author = author_data.get(
                        "name",
                        "Unknown"
                    )

                elif isinstance(author_data, list):

                    names = []

                    for a in author_data:

                        if isinstance(a, dict):

                            names.append(
                                a.get("name", "")
                            )

                    author = ", ".join(names)

                # SERVINGS
                servings = data.get(
                    "recipeYield",
                    "Unknown"
                )

                break

        except Exception as e:

            print("JSON error:", e)

            continue

    return {

        "Title": title,

        "Ingredients": ingredients,

        "Steps": steps,

        "Author": author,

        "Servings": servings,

        "Link": url

    }

driver = start_driver()

# ======================
# AMBIL LINK RESEP
# ======================

recipe_links = scrape_recipe_links(
    driver,
    query="masakan indonesia"
)

# ======================
# SCRAPE DETAIL
# ======================

all_data = []

for i, link in enumerate(recipe_links[:100]):

    try:

        print(f"[{i+1}] Scraping:", link)

        data = get_recipe_detail(
            driver,
            link
        )

        all_data.append(data)

    except Exception as e:

        print("Error:", e)

# ======================
# CLOSE DRIVER
# ======================

driver.quit()

# ======================
# DATAFRAME
# ======================

df = pd.DataFrame(all_data)

# hapus duplicate
df.drop_duplicates(
    subset=["Link"],
    inplace=True
)

df.reset_index(
    drop=True,
    inplace=True
)

# ======================
# SAVE CSV
# ======================

df.to_csv(
    "cookpad_recipes.csv",
    index=False,
    encoding="utf-8-sig"
)

print("✅ SELESAI")
print(df.head())