from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pandas as pd

# Carica il dataset dei laptop (modifica il percorso se necessario)
try:
    df_laptops = pd.read_csv('./dataset/laptops.csv')
except FileNotFoundError:
    df_laptops = pd.DataFrame()

class ActionSearchLaptop(Action):
    def name(self) -> Text:
        return "laptop_search_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Estrai i valori dei slot
        brand = tracker.get_slot('brand')
        price_min = tracker.get_slot('price_min')
        price_max = tracker.get_slot('price_max')
        processor_brand = tracker.get_slot('processor_brand')
        processor_name = tracker.get_slot('processor_name')
        ram_gb = tracker.get_slot('ram_gb')
        ssd_gb = tracker.get_slot('ssd_gb')
        hdd_gb = tracker.get_slot('hdd_gb')
        gpu_brand = tracker.get_slot('gpu_brand')
        GPU = tracker.get_slot('GPU')
        display_inch = tracker.get_slot('display_inch')
        battery_hrs = tracker.get_slot('battery_hrs')

        # Controlli sui valori inseriti
        errors = []
        # Controlli numerici
        numeric_slots = {
            'price_min': price_min,
            'price_max': price_max,
            'ram_gb': ram_gb,
            'ssd_gb': ssd_gb,
            'hdd_gb': hdd_gb,
            'display_inch': display_inch,
            'battery_hrs': battery_hrs
        }
        for name, value in numeric_slots.items():
            if value is not None:
                try:
                    val = float(value)
                    if val < 0:
                        errors.append(f"Il valore di {name} deve essere positivo.")
                except ValueError:
                    errors.append(f"Il valore di {name} non è un numero valido.")
        # Controllo coerenza prezzo
        if price_min is not None and price_max is not None:
            try:
                if float(price_min) > float(price_max):
                    errors.append("Il prezzo minimo non può essere maggiore del prezzo massimo.")
            except ValueError:
                pass

        if errors:
            dispatcher.utter_message(text="Sono stati rilevati alcuni problemi con i valori inseriti:\n- " + "\n- ".join(errors))
            # Non procedere, lascia il form attivo
            return []

        # Filtra il DataFrame
        df = df_laptops.copy()
        if brand:
            df = df[df['brand'].str.lower() == brand.lower()]
        if price_min:
            df = df[df['price'] >= float(price_min)]
        if price_max:
            df = df[df['price'] <= float(price_max)]
        if processor_brand:
            df = df[df['processor_brand'].str.lower() == processor_brand.lower()]
        if processor_name:
            df = df[df['processor_name'].str.lower() == processor_name.lower()]
        if ram_gb:
            df = df[df['ram_gb'] >= float(ram_gb)]
        if ssd_gb:
            df = df[df['ssd_gb'] >= float(ssd_gb)]
        if hdd_gb:
            df = df[df['hdd_gb'] >= float(hdd_gb)]
        if gpu_brand:
            df = df[df['gpu_brand'].str.lower() == gpu_brand.lower()]
        if GPU:
            df = df[df['GPU'].str.lower() == GPU.lower()]
        if display_inch:
            df = df[df['display_inch'] >= float(display_inch)]
        if battery_hrs:
            df = df[df['battery_hrs'] >= float(battery_hrs)]

        # Risultati
        if df.empty:
            dispatcher.utter_message(text="Mi dispiace, non ho trovato laptop che corrispondano ai tuoi filtri.")
        else:
            messages = []
            for _, r in df.head(5).iterrows():
                msg = (
                    f"Modello: {r['name']}\n"
                    f"Marca: {r['brand']}\n"
                    f"Prezzo: {r['price']}€\n"
                    f"Processore: {r['processor_name']} ({r['processor_brand']}) - {r['ghz']} GHz\n"
                    f"RAM: {r['ram_gb']} GB ({r['ram_type']}, espandibile fino a {r['ram_expandable_gb']} GB)\n"
                    f"Storage: {r['ssd_gb']} GB SSD + {r['hdd_gb']} GB HDD\n"
                    f"GPU: {r['GPU']} ({r['gpu_brand']})\n"
                    f"Display: {r['display_type']} - {r['display_inch']} pollici\n"
                    f"Autonomia: {r['battery_hrs']} ore\n"
                    f"Alimentatore: {r['adapter_w']} W"
                )
                messages.append(msg)
            dispatcher.utter_message(text="\n\n".join(messages))

        # Reset slot
        return [
            SlotSet('brand', None),
            SlotSet('price_min', None),
            SlotSet('price_max', None),
            SlotSet('processor_brand', None),
            SlotSet('processor_name', None),
            SlotSet('ram_gb', None),
            SlotSet('ssd_gb', None),
            SlotSet('hdd_gb', None),
            SlotSet('gpu_brand', None),
            SlotSet('GPU', None),
            SlotSet('display_inch', None),
            SlotSet('battery_hrs', None)
        ]