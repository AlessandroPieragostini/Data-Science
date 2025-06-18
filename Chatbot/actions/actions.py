from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import pandas as pd

# Carica il dataset dei laptop
try:
    df_laptops = pd.read_csv('./dataset/laptop.csv')
except FileNotFoundError:
    df_laptops = pd.DataFrame()
    


class ValidateLaptopSearchForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_laptop_search_form"

    def _validate_positive(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        slot_name: str,
        prompt: str,
    ) -> Dict[Text, Any]:
        try:
            value = float(slot_value)
            if value < 0:
                dispatcher.utter_message(template=prompt)
                return {slot_name: None}
            return {slot_name: value}
        except (TypeError, ValueError):
            dispatcher.utter_message(template=prompt)
            return {slot_name: None}

    def validate_price_min(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        return self._validate_positive(slot_value, dispatcher, "price_min", "utter_ask_price_min")

    def validate_price_max(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        # controllo anche coerenza con price_min
        validated = self._validate_positive(slot_value, dispatcher, "price_max", "utter_ask_price_max")
        if validated.get("price_max") is not None:
            min_p = tracker.get_slot("price_min")
            if min_p is not None and float(validated["price_max"]) < float(min_p):
                dispatcher.utter_message(template="utter_ask_price_max")
                return {"price_max": None}
        return validated

    def validate_ram_gb(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        return self._validate_positive(slot_value, dispatcher, "ram_gb", "utter_ask_ram_gb")

    def validate_ssd_gb(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        return self._validate_positive(slot_value, dispatcher, "ssd_gb", "utter_ask_ssd_gb")

    def validate_hdd_gb(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        return self._validate_positive(slot_value, dispatcher, "hdd_gb", "utter_ask_hdd_gb")

    def validate_display_inch(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        return self._validate_positive(slot_value, dispatcher, "display_inch", "utter_ask_display_inch")

    def validate_battery_hrs(
        self, slot_value, dispatcher, tracker, domain
    ) -> Dict[Text, Any]:
        return self._validate_positive(slot_value, dispatcher, "battery_hrs", "utter_ask_battery_hrs")


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
        gpu = tracker.get_slot('gpu')
        display_inch = tracker.get_slot('display_inch')
        battery_hrs = tracker.get_slot('battery_hrs')

        # Filtra il DataFrame
        df = df_laptops.copy()
        if brand:
            df = df[df['brand'].str.lower() == brand.lower()]
        if price_min is not None:
            df = df[df['price'] >= float(price_min)]
        if price_max is not None:
            df = df[df['price'] <= float(price_max)]
        if processor_brand:
            df = df[df['processor_brand'].str.lower() == processor_brand.lower()]
        if processor_name:
            df = df[df['processor_name'].str.lower() == processor_name.lower()]
        if ram_gb is not None:
            df = df[df['ram_gb'] >= float(ram_gb)]
        if ssd_gb is not None:
            df = df[df['ssd_gb'] >= float(ssd_gb)]
        if hdd_gb is not None:
            df = df[df['hdd_gb'] >= float(hdd_gb)]
        if gpu_brand:
            df = df[df['gpu_brand'].str.lower() == gpu_brand.lower()]
        if gpu:
            df = df[df['gpu'].str.lower() == gpu.lower()]
        if display_inch is not None:
            df = df[df['display_inch'] >= float(display_inch)]
        if battery_hrs is not None:
            df = df[df['battery_hrs'] >= float(battery_hrs)]

        # Risultati
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
                    f"GPU: {r['GPU']} ({r['gpu_brand']})\n"
                    f"Display: {r['display_type']} - {r['display_inch']}\" pollici\n"
                    f"Autonomia: {r['battery_hrs']} ore\n"
                    f"Alimentatore: {r['adapter_w']} W"
                ))

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
            SlotSet('gpu', None),
            SlotSet('display_inch', None),
            SlotSet('battery_hrs', None)
        ]
