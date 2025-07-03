from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pandas as pd

# Carica il dataset dei laptop
df_laptops = pd.DataFrame()
try:
    df_laptops = pd.read_csv('./dataset/laptop.csv')
except FileNotFoundError:
    pass


# --- Validazione centralizzata con re-ask o avanzamento ---
class ValidateLaptopSearchForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_laptop_search_form"

    def _validate_positive(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        slot_name: str,
        invalid_prompt: str,
    ) -> Dict[Text, Any]:
        try:
            value = float(slot_value)
            if value < 0:
                dispatcher.utter_message(template=invalid_prompt)
                return {slot_name: None}
            return {slot_name: value}
        except (TypeError, ValueError):
            dispatcher.utter_message(template=invalid_prompt)
            return {slot_name: None}

    def validate_price_max(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        result = self._validate_positive(slot_value, dispatcher, "price_max", "utter_price_max_invalid")
        if result.get("price_max") is not None:
            min_p = tracker.get_slot("price_min")
            if min_p is not None and float(result["price_max"]) < float(min_p):
                dispatcher.utter_message(template="utter_price_max_invalid")
                return {"price_max": None}
        return result

    def validate_ram_gb(self, slot_value, dispatcher, tracker, domain):
        return self._validate_positive(slot_value, dispatcher, "ram_gb", "utter_ram_gb_invalid")

    def validate_ssd_gb(self, slot_value, dispatcher, tracker, domain):
        return self._validate_positive(slot_value, dispatcher, "ssd_gb", "utter_ssd_gb_invalid")

    def validate_hdd_gb(self, slot_value, dispatcher, tracker, domain):
        return self._validate_positive(slot_value, dispatcher, "hdd_gb", "utter_hdd_gb_invalid")

    def validate_display_inch(self, slot_value, dispatcher, tracker, domain):
        return self._validate_positive(slot_value, dispatcher, "display_inch", "utter_display_inch_invalid")

    def validate_battery_hrs(self, slot_value, dispatcher, tracker, domain):
        return self._validate_positive(slot_value, dispatcher, "battery_hrs", "utter_battery_hrs_invalid")


class ActionRecapFilters(Action):
    def name(self) -> Text:
        return "action_recap_filters"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Ottieni i valori dei filtri settati finora
        filter_slots = [
            "brand",  "price_max", "processor_brand",
            "processor_name", "ram_gb", "ssd_gb", "hdd_gb",
            "gpu_brand", "gpu", "display_inch", "battery_hrs"
        ]

        applied_filters = []
        for slot in filter_slots:
            value = tracker.get_slot(slot)
            if value is not None:
                applied_filters.append(f"{slot.replace('_', ' ').capitalize()}: {value}")

        if applied_filters:
            filters_text = "\n- " + "\n- ".join(applied_filters)
            dispatcher.utter_message(text=f"Hai applicato i seguenti filtri finora:{filters_text}")
        else:
            dispatcher.utter_message(text="Non hai ancora applicato nessun filtro.")

        # Chiedi all'utente cosa vuole fare
        dispatcher.utter_message(text="Vuoi aggiungere altri filtri o avviare la ricerca?")

        return []

# --- Azione di ricerca finale ---
class ActionSearchLaptop(Action):
    def name(self) -> Text:
        return "action_search_laptop"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        if df_laptops.empty:
            dispatcher.utter_message(text="Errore interno: dataset dei laptop non disponibile.")
            return []

        # Estrazione dei valori dei slot
        brand = tracker.get_slot('brand')
        price_max = tracker.get_slot('price_max')
        processor_brand = tracker.get_slot('processor_brand')
        processor_name = tracker.get_slot('processor_name')
        ram_gb = tracker.get_slot('ram_gb')
        ssd_gb = tracker.get_slot('ssd_gb')
        hdd_gb = tracker.get_slot('hdd_gb')
        gpu_brand = tracker.get_slot('gpu_brand')
        gpu = tracker.get_slot('gpu')
        display_inch = tracker.get_slot('display_inch')
        battery_hrs = tracker.get_slot('battery_hrs')

        # Filtra il DataFrame
        df = df_laptops.copy()
        if brand:
            df = df[df['brand'].str.lower().str.contains(brand.lower())]
        if price_max is not None:
            df = df[df['price'] <= float(price_max)]
        if processor_brand:
            df = df[df['processor_brand'].str.lower().str.contains(processor_brand.lower())]
        if processor_name:
            df = df[df['processor_name'].str.lower().str.contains(processor_name.lower())]
        if ram_gb is not None:
            df = df[df['ram_gb'] >= float(ram_gb)]
        if ssd_gb is not None:
            df = df[df['ssd_gb'] >= float(ssd_gb)]
        if hdd_gb is not None:
            df = df[df['hdd_gb'] >= float(hdd_gb)]
        if gpu_brand:
            df = df[df['gpu_brand'].str.lower().str.contains(gpu_brand.lower())]
        if gpu:
            df = df[df['gpu'].str.lower().str.contains(gpu.lower())]
        if display_inch is not None:
            df = df[df['display_inch'] >= float(display_inch)]
        if battery_hrs is not None:
            df = df[df['battery_hrs'] >= float(battery_hrs)]

        # Mostra i risultati
        if df.empty:
            dispatcher.utter_message(text="Mi dispiace, non ho trovato laptop che corrispondano ai tuoi filtri.")
        else:
            for _, r in df.head(5).iterrows():
                dispatcher.utter_message(text=(
                    f"Modello: {r['name']}\n"
                    f"Marca: {r['brand']}\n"
                    f"Prezzo: {r['price']}€\n"
                    f"Processore: {r['processor_name']} ({r['processor_brand']}) - {r['ghz']} GHz\n"
                    f"RAM: {r['ram_gb']} GB ({r['ram_type']}, espandibile fino a {r['ram_expandable_gb']} GB)\n"
                    f"Storage: {r['ssd_gb']} GB SSD + {r['hdd_gb']} GB HDD\n"
                    f"GPU: {r['gpu']} ({r['gpu_brand']})\n"
                    f"Display: {r['display_type']} - {r['display_inch']}\" pollici\n"
                    f"Autonomia: {r['battery_hrs']} ore\n"
                    f"Alimentatore: {r['adapter_w']} W\n"
                    + "="*100
                ))

        # Reset dei slot
        slots_to_reset = [
            'brand', 'price_max', 'processor_brand', 'processor_name',
            'ram_gb', 'ssd_gb', 'hdd_gb', 'gpu_brand', 'gpu', 'display_inch', 'battery_hrs'
        ]
        return [SlotSet(slot, None) for slot in slots_to_reset]
