from tkinter import EventType
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
        page = tracker.get_slot('page')  # Nuovo slot page

        # Default a 1 se page non è valorizzato o non valido
        try:
            page_num = int(page)
            if page_num < 1:
                page_num = 1
        except (TypeError, ValueError):
            page_num = 1

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

        # Calcola range di righe da mostrare in base a page_num
        page_size = 5
        start_idx = (page_num - 1) * page_size
        end_idx = start_idx + page_size

        # Mostra i risultati
        if df.empty:
            dispatcher.utter_message(text="Mi dispiace, non ho trovato laptop che corrispondano ai tuoi filtri.")
        else:
            dispatcher.utter_message(text=f"📄 Risultati - Pagina {page_num}:")
            subset = df.iloc[start_idx:end_idx]
            if subset.empty:
                dispatcher.utter_message(text="Non ci sono più risultati da mostrare per questa pagina.")
            else:
                for _, r in subset.iterrows():
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

        # Reset dei slot, se vuoi mantenere il page (per navigazione avanti/indietro) NON resettarlo
        
        return []

class ActionIncrementPage(Action):
    def name(self) -> Text:
        return "action_increment_page"

    def run(self, dispatcher, tracker, domain):
        current_page = tracker.get_slot("page")
        try:
            page_num = int(current_page)
            if page_num < 1:
                page_num = 1
        except (TypeError, ValueError):
            page_num = 1

        new_page = page_num + 1
        # Aggiorna slot page
        return [SlotSet("page", new_page), SlotSet("requested_slot", None)]
    
class ActionResetFilters(Action):
    """
    Action che azzera i filtri specificati.
    """
    def name(self) -> Text:
        return "action_reset_filters"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[EventType]:
        # Lista degli slot da resettare
        slots_to_reset = [
            'brand',
            'price_max',
            'processor_brand',
            'processor_name',
            'ram_gb',
            'ssd_gb',
            'hdd_gb',
            'gpu_brand',
            'gpu',
            'display_inch',
            'battery_hrs'
        ]

        # Genera eventi SlotSet per azzerare ogni slot
        events = [SlotSet(slot, None) for slot in slots_to_reset]

        # Messaggio di conferma
        dispatcher.utter_message(text="Ho azzerato tutti i filtri.")

        return events
    
class ActionSuggestBestLaptop(Action):
    """
    Suggerisce il laptop che meglio si adatta ai filtri, in base a un criterio di ranking.
    """
    def name(self) -> Text:
        return "action_suggest_best_laptop"

    def run(self,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:
        # Esempio: ranking sul prezzo più basso
        params = {k: v for k, v in tracker.current_slot_values().items() if v is not None}
        # Mock dei risultati
        products = [
            {"name": "Laptop Ultra", "price": 1100},
            {"name": "EcoBook", "price": 850}
        ]
        best = sorted(products, key=lambda x: x['price'])[0]
        dispatcher.utter_message(text=f"Ti consiglio il modello {best['name']} al prezzo di €{best['price']}.")
        return []
    
class ActionSearchCheapestLaptop(Action):
    """
    Cerca il laptop più economico in base ai filtri e lo propone.
    """
    def name(self) -> Text:
        return "action_search_cheapest_laptop"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Controllo dataset
        try:
            df = df_laptops.copy()
        except NameError:
            dispatcher.utter_message(text="Errore interno: dataset dei laptop non disponibile.")
            return []

        # Estrazione e applicazione filtri (stessa logica di ActionSearchLaptop)
        filters = {
            'brand': tracker.get_slot('brand'),
            'price_max': tracker.get_slot('price_max'),
            'processor_brand': tracker.get_slot('processor_brand'),
            'processor_name': tracker.get_slot('processor_name'),
            'ram_gb': tracker.get_slot('ram_gb'),
            'ssd_gb': tracker.get_slot('ssd_gb'),
            'hdd_gb': tracker.get_slot('hdd_gb'),
            'gpu_brand': tracker.get_slot('gpu_brand'),
            'gpu': tracker.get_slot('gpu'),
            'display_inch': tracker.get_slot('display_inch'),
            'battery_hrs': tracker.get_slot('battery_hrs')
        }
        # Filtro come sopra
        if filters['brand']:
            df = df[df['brand'].str.lower().str.contains(filters['brand'].lower())]
        if filters['price_max'] is not None:
            df = df[df['price'] <= float(filters['price_max'])]
        if filters['processor_brand']:
            df = df[df['processor_brand'].str.lower().str.contains(filters['processor_brand'].lower())]
        if filters['processor_name']:
            df = df[df['processor_name'].str.lower().str.contains(filters['processor_name'].lower())]
        if filters['ram_gb'] is not None:
            df = df[df['ram_gb'] >= float(filters['ram_gb'])]
        if filters['ssd_gb'] is not None:
            df = df[df['ssd_gb'] >= float(filters['ssd_gb'])]
        if filters['hdd_gb'] is not None:
            df = df[df['hdd_gb'] >= float(filters['hdd_gb'])]
        if filters['gpu_brand']:
            df = df[df['gpu_brand'].str.lower().str.contains(filters['gpu_brand'].lower())]
        if filters['gpu']:
            df = df[df['gpu'].str.lower().str.contains(filters['gpu'].lower())]
        if filters['display_inch'] is not None:
            df = df[df['display_inch'] >= float(filters['display_inch'])]
        if filters['battery_hrs'] is not None:
            df = df[df['battery_hrs'] >= float(filters['battery_hrs'])]

        if df.empty:
            dispatcher.utter_message(text="Mi dispiace, non ho trovato alcun laptop con quei filtri.")
            return []

        # Seleziona quello con prezzo minimo
        cheapest = df.loc[df['price'].idxmin()]
        dispatcher.utter_message(text=(
            f"Il laptop più economico che ho trovato è:\n"
            f"Modello: {cheapest['name']}\n"
            f"Marca: {cheapest['brand']}\n"
            f"Prezzo: {cheapest['price']}€\n"
            f"Processore: {cheapest['processor_name']} ({cheapest['processor_brand']})\n"
            f"RAM: {cheapest['ram_gb']} GB\n"
        ))
        return []