import json
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


def _get_text_or_none(driver, by, value):
    """Safe element text getter."""
    try:
        el = driver.find_element(by, value)
        return el.text.strip()
    except NoSuchElementException:
        return None


def _get_child_text_or_none(parent, by, value):
    try:
        el = parent.find_element(by, value)
        return el.text.strip()
    except NoSuchElementException:
        return None


def imd_scraper(tool_input: dict) -> str:
    """
    Scrape structured weather data from IMD 'responsive' city page.

    Input:
        tool_input = {"station_id": 42971}

    Returns:
        JSON string with structure:

        {
          "station_id": 42971,
          "url": "...",
          "source": "IMD_SELENIUM",
          "scraped_at_utc": "...",
          "date_info": {...},
          "past_24_hours": {...},
          "sun_moon": {...},
          "forecast_7_days": [ {...}, ... ]
        }
    """

    station_id = tool_input.get("station_id")
    if not station_id:
        return json.dumps({"error": "station_id missing"})

    url = f"https://city.imd.gov.in/citywx/responsive/?id={station_id}"

    # ---- set up selenium driver (headless chrome) ----
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        # allow JS to load everything
        time.sleep(4)

        result = {
            "station_id": station_id,
            "url": url,
            "source": "IMD_SELENIUM",
            "scraped_at_utc": datetime.utcnow().isoformat() + "Z",
            "date_info": {},
            "past_24_hours": {},
            "sun_moon": {},
            "forecast_7_days": []
        }

        # ------------------------------------------------------------------
        # 1) DATE INFO  (day name + full date)
        # ------------------------------------------------------------------
        # From your screenshot:
        # <span>Monday</span>
        # <span>December 01, 2025</span>
        try:
            date_span = driver.find_element(
                By.XPATH,
                "//span[contains(text(), ',') and contains(text(),'20')]"
            )
            full_date = date_span.text.strip()
            try:
                day_span = date_span.find_element(
                    By.XPATH, "./preceding-sibling::span[1]"
                )
                day_name = day_span.text.strip()
            except NoSuchElementException:
                day_name = None

            result["date_info"] = {
                "day": day_name,
                "full_date": full_date
            }
        except NoSuchElementException:
            result["date_info"] = {}

        # ------------------------------------------------------------------
        # 2) PAST 24 HOURS OVERVIEW
        # ------------------------------------------------------------------
        # HTML (simplified):
        # <p>Weather<br>Past 24 Hours Overview</p>
        # <ul>
        #   <li> "Maximum | Dep" ... <span>1730 IST</span> <p>28.2°C | -2.0</p>
        #   <li> "Minimum | Dep" ... <span>0830 IST</span> <p>16.0°C | 1.2</p>
        #   <li> "Rainfall" ... <span>0830 IST</span> <p>000.0mm</p>
        #   <li> "Humidity" ... <span>1730 IST | 0830 IST</span> <p>68% | 66%</p>
        past_24 = {
            "maximum": None,
            "minimum": None,
            "rainfall": None,
            "humidity": None,
        }

        try:
            ul = driver.find_element(
                By.XPATH,
                "//p[contains(.,'Past 24 Hours Overview')]/following-sibling::ul"
            )
            li_blocks = ul.find_elements(By.XPATH, "./li")
            for li in li_blocks:
                li_text = li.text

                # MAXIMUM
                if "Maximum" in li_text:
                    time_ist = _get_child_text_or_none(li, By.TAG_NAME, "span")
                    p_text = _get_child_text_or_none(li, By.TAG_NAME, "p") or ""
                    parts = p_text.replace("|", " ").split()
                    # e.g. ["28.2°C", "-2.0"]
                    max_val = parts[0] if len(parts) > 0 else None
                    max_dep = parts[1] if len(parts) > 1 else None
                    past_24["maximum"] = {
                        "value": max_val,
                        "departure": max_dep,
                        "time_ist": time_ist
                    }

                # MINIMUM
                elif "Minimum" in li_text:
                    time_ist = _get_child_text_or_none(li, By.TAG_NAME, "span")
                    p_text = _get_child_text_or_none(li, By.TAG_NAME, "p") or ""
                    parts = p_text.replace("|", " ").split()
                    min_val = parts[0] if len(parts) > 0 else None
                    min_dep = parts[1] if len(parts) > 1 else None
                    past_24["minimum"] = {
                        "value": min_val,
                        "departure": min_dep,
                        "time_ist": time_ist
                    }

                # RAINFALL
                elif "Rainfall" in li_text:
                    time_ist = _get_child_text_or_none(li, By.TAG_NAME, "span")
                    p_text = _get_child_text_or_none(li, By.TAG_NAME, "p") or ""
                    mm = None
                    for tok in p_text.split():
                        if "mm" in tok:
                            mm = tok
                            break
                    past_24["rainfall"] = {
                        "value": mm,
                        "time_ist": time_ist
                    }

                # HUMIDITY
                elif "Humidity" in li_text:
                    # pattern should contain two % values
                    p_text = _get_child_text_or_none(li, By.TAG_NAME, "p") or ""
                    percents = [t for t in p_text.split() if "%" in t]
                    hum_m = percents[0] if len(percents) > 0 else None
                    hum_e = percents[1] if len(percents) > 1 else None
                    past_24["humidity"] = {
                        "morning": hum_m,
                        "evening": hum_e
                    }

            result["past_24_hours"] = past_24

        except NoSuchElementException:
            # leave defaults (None)
            pass

        # ------------------------------------------------------------------
        # 3) SUN & MOON INFO
        # ------------------------------------------------------------------
        # From your screenshot:
        # <h3>17:05</h3><p>Sunset (Today)</p>
        # <h3>06:05</h3><p>Sunrise (Tomorrow)</p>
        # <h3>13:16</h3><p>Moonrise</p>
        # <h3>--:--</h3><p>Moonset</p>  (for example)
        def get_time_for(label: str):
            try:
                p = driver.find_element(By.XPATH, f"//p[contains(text(),'{label}')]")
                h3 = p.find_element(By.XPATH, "./preceding-sibling::h3[1]")
                return h3.text.strip()
            except NoSuchElementException:
                return None

        sun_moon = {
            "sunset_today": get_time_for("Sunset (Today)"),
            "sunrise_tomorrow": get_time_for("Sunrise (Tomorrow)"),
            "moonrise": get_time_for("Moonrise"),
            "moonset": get_time_for("Moonset"),
        }
        result["sun_moon"] = sun_moon

        # ------------------------------------------------------------------
        # 4) 7 DAYS FORECAST
        # ------------------------------------------------------------------
        # HTML (per card, simplified):
        # <div class="min-h-32 ...">
        #   <span>1-DEC</span>
        #   <h3>Temperature <span class="float-end">Humidity</span></h3>
        #   <h3>29 16</h3>
        #   <span class="float-end">0 0</span>
        #   <h3>Forecast</h3>
        #   <p>Partly cloudy sky</p>
        # </div>
        forecast_list = []
        try:
            forecast_container = driver.find_element(
                By.XPATH,
                "//p[contains(.,'7 days forecast')]/following-sibling::div"
            )
            cards = forecast_container.find_elements(
                By.XPATH,
                ".//div[contains(@class,'min-h-32')]"
            )

            for card in cards:
                try:
                    date_text = card.find_element(
                        By.XPATH,
                        ".//span[contains(@class,'text-blue-700')]"
                    ).text.strip()
                except NoSuchElementException:
                    date_text = None

                # second h3 inside card holds numbers (29 16)
                h3s = card.find_elements(By.TAG_NAME, "h3")
                temp_max = temp_min = None
                if len(h3s) >= 2:
                    num_tokens = h3s[1].text.split()
                    if len(num_tokens) >= 2:
                        temp_max, temp_min = num_tokens[0], num_tokens[1]

                # last span.float-end in card holds humidity numbers (0 0)
                hum_max = hum_min = None
                spans_float = card.find_elements(
                    By.XPATH,
                    ".//span[contains(@class,'float-end')]"
                )
                if spans_float:
                    hum_tokens = spans_float[-1].text.split()
                    if len(hum_tokens) >= 2:
                        hum_max, hum_min = hum_tokens[0], hum_tokens[1]

                # forecast description paragraph
                condition = _get_child_text_or_none(
                    card,
                    By.XPATH,
                    ".//p[contains(@class,'text-gray-600')]"
                )

                forecast_list.append({
                    "date": date_text,
                    "temp_max": temp_max,
                    "temp_min": temp_min,
                    "humidity_max": hum_max,
                    "humidity_min": hum_min,
                    "condition": condition
                })

            result["forecast_7_days"] = forecast_list

        except NoSuchElementException:
            result["forecast_7_days"] = []

        # ------------------------------------------------------------------
        # DONE
        # ------------------------------------------------------------------
        return json.dumps(result)

    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        driver.quit()
