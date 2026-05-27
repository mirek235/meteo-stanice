import requests
import tinytuya

API_KEY = "fjyra54x3cxntrtnxwyx"
API_SECRET = "749e64c1ecf540aab94079d81261b7a0"
DEVICE_ID = "36768866e8db84bd949d"

TUYA_PATH = f"/v2.0/cloud/thing/{DEVICE_ID}/shadow/properties"

try:
    c = tinytuya.Cloud(apiRegion="eu", apiKey=API_KEY, apiSecret=API_SECRET)
    data = c.cloudrequest(TUYA_PATH)

    if data and data.get("success"):
        result = data.get("result", {})
        properties = result.get("properties", [])

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

        t_kuchyn = ziskej_teplotu("Tin")
        t_venku = ziskej_teplotu("ToutCh1")
        t_loznice = ziskej_teplotu("ToutCh2")
        t_koupelna = ziskej_teplotu("ToutCh3")

        h_kuchyn = ziskej_vlhkost("Hin")
        h_venku = ziskej_vlhkost("HoutCh1")
        h_loznice = ziskej_vlhkost("HoutCh2")
        h_koupelna = ziskej_vlhkost("HoutCh3")

        # A) ŽIVÝ OBRAZ
        zivy_obraz_url = (
            f"https://in.zivyobraz.eu/?import_key=1p4KagnocYwhXHtB"
            f"&teplota_kuchyne={t_kuchyn}&vlhkost_kuchyne={h_kuchyn}"
            f"&teplota_venku={t_venku}&vlhkost_venku={h_venku}"
            f"&teplota_loznice={t_loznice}&vlhkost_loznice={h_loznice}"
            f"&teplota_koupelny={t_koupelna}&vlhkost_koupelny={h_koupelna}"
        )
        requests.get(zivy_obraz_url)

        # B) TMEP KUCHYŇ
        if t_kuchyn is not None and h_kuchyn is not None:
            requests.get(f"http://pechmanovych-in.tmep.cz/?temp={t_kuchyn}&humV={h_kuchyn}")

        # C) TMEP VENKU
        if t_venku is not None and h_venku is not None:
            requests.get(f"http://pechmanovych-out.tmep.cz/?temp={t_venku}&humV={h_venku}")

        print("Data úspěšně odeslána na Živý obraz i TMEP.")
    else:
        print("Chyba Tuya:", data.get("msg") if data else "Žádná odpověď")
except Exception as e:
    print("Neočekávaná chyba:", e)
