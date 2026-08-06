import os
import requests
import tinytuya

# Stažení zabezpečených klíčů a domén z GitHub Secrets
API_KEY = os.environ.get("TUYA_API_KEY")
API_SECRET = os.environ.get("TUYA_API_SECRET")
DEVICE_ID = os.environ.get("TUYA_DEVICE_ID")
ZIVY_OBRAZ_KEY = os.environ.get("ZIVY_OBRAZ_KEY")
TMEP_DOMAIN_IN = os.environ.get("TMEP_DOMAIN_IN")
TMEP_DOMAIN_OUT = os.environ.get("TMEP_DOMAIN_OUT")

TUYA_PATH = f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties"

try:
    c = tinytuya.Cloud(apiRegion="eu", apiKey=API_KEY, apiSecret=API_SECRET)
    data = c.cloudrequest(TUYA_PATH)

    if data and data.get("success"):
        result = data.get("result", {})
        properties = result.get("properties", [])

        # Pomocné funkce
        def ziskej_teplotu(kod_senzoru):
            sensor = next((item for item in properties if item.get("code") == kod_senzoru), None)
            if sensor and "value" in sensor:
                return round((sensor["value"] / 10 - 32) * 5 / 9, 1)
            return None

        def ziskej_vlhkost(kod_senzoru):
            sensor = next((item for item in properties if item.get("code") == kod_senzoru), None)
            if sensor and "value" in sensor:
                return sensor["value"]
            return None

        def ziskej_tlak():
            for kod in ["pressure", "pressure_value", "pressure_bar", "pres"]:
                sensor = next((item for item in properties if item.get("code") == kod), None)
                if sensor and "value" in sensor:
                    val = sensor["value"]
                    return round(val / 10, 1) if val > 5000 else val
            return None

        # Načtení dat ze senzorů
        t_kuchyn = ziskej_teplotu("Tin")
        t_venku = ziskej_teplotu("ToutCh1")
        t_loznice = ziskej_teplotu("ToutCh2")
        t_koupelna = ziskej_teplotu("ToutCh3")

        h_kuchyn = ziskej_vlhkost("Hin")
        h_venku = ziskej_vlhkost("HoutCh1")
        h_loznice = ziskej_vlhkost("HoutCh2")
        h_koupelna = ziskej_vlhkost("HoutCh3")

        tlak = ziskej_tlak()

        # A) ODESLÁNÍ - ŽIVÝ OBRAZ
        if ZIVY_OBRAZ_KEY:
            zivy_obraz_url = (
                f"https://in.zivyobraz.eu/?import_key={ZIVY_OBRAZ_KEY}"
                f"&teplota_kuchyne={t_kuchyn}&vlhkost_kuchyne={h_kuchyn}"
                f"&teplota_venku={t_venku}&vlhkost_venku={h_venku}"
                f"&teplota_loznice={t_loznice}&vlhkost_loznice={h_loznice}"
                f"&teplota_koupelny={t_koupelna}&vlhkost_koupelny={h_koupelna}"
            )
            if tlak:
                zivy_obraz_url += f"&tlak={tlak}"
            requests.get(zivy_obraz_url)

        # B) ODESLÁNÍ - TMEP KUCHYŇ
        if t_kuchyn is not None and h_kuchyn is not None and TMEP_DOMAIN_IN:
            tmep_in_url = f"http://{TMEP_DOMAIN_IN}.tmep.cz/?temp={t_kuchyn}&humV={h_kuchyn}"
            if tlak:
                tmep_in_url += f"&pressV={tlak}"
            requests.get(tmep_in_url)

        # C) ODESLÁNÍ - TMEP VENKU
        if t_venku is not None and h_venku is not None and TMEP_DOMAIN_OUT:
            tmep_out_url = f"http://{TMEP_DOMAIN_OUT}.tmep.cz/?temp={t_venku}&humV={h_venku}"
            requests.get(tmep_out_url)

        print("Data úspěšně odeslána na Živý obraz i TMEP. Tlak nalezen:", tlak)
    else:
        print("Chyba komunikace s Tuya Cloudem:", data.get("msg") if data else "Žádná odpověď")

except Exception as e:
    print("Neočekávaná chyba:", e)

