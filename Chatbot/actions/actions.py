from typing import Any, Dict, List
import pandas as pd
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Carica il DataFrame dal CSV
df = pd.read_csv("./dataset/laptop.csv").fillna("Dato non disponibile")

# Dizionario per memorizzare i preferiti degli utenti
user_favorites = {}

# Funzione di filtro laptop
def match_laptop(filters: Dict[str, Any]) -> pd.DataFrame:
    query = df.copy()

    if filters.get("prezzo_min"):
        query = query[query["price"] >= float(filters["prezzo_min"])]

    if filters.get("prezzo_max"):
        query = query[query["price"] <= float(filters["prezzo_max"])]

    if filters.get("marca"):
        query = query[query["brand"].str.lower().str.contains(filters["marca"].lower())]

    if filters.get("ram"):
        query = query[query["ram_gb"]>= float(filters["ram"])]

    if filters.get("storage"):
        query = query[
            query["ssd_gb"]>= float(filters["storage"])  |
            query["hdd_gb"]>= float(filters["storage"])
        ]

    if filters.get("processore"):
        query = query[query["processor_name"].str.lower().str.contains(filters["processore"].lower())]

    if filters.get("gpu"):
        query = query[query["GPU"].str.lower().str.contains(filters["gpu"].lower())]

    if filters.get("dimensione_schermo"):
        query = query[query["display_inch"]>= float(filters["dimensione_schermo"]) ]

    if filters.get("display"):
        query = query[query["display_type"].str.lower().str.contains(filters["display"].lower())]

    if filters.get("battery_life"):
        query = query[query["battery_hrs"] >= float(filters["battery_life"])]

    return query


class ActionFiltraLaptop(Action):
    def name(self) -> str:
        return "action_filtra_laptop"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        filters = {
            "marca": tracker.get_slot("marca"),
            "ram": tracker.get_slot("ram"),
            "storage": tracker.get_slot("storage"),
            "processore": tracker.get_slot("processore"),
            "gpu": tracker.get_slot("gpu"),
            "dimensione_schermo": tracker.get_slot("dimensione_schermo"),
            "display": tracker.get_slot("display"),
            "battery_life": tracker.get_slot("battery_life"),
            "prezzo_min": tracker.get_slot("prezzo_min"),
            "prezzo_max": tracker.get_slot("prezzo_max"),
        }

        results = match_laptop(filters)
        message = (f"{filters['prezzo_min']} - {filters['prezzo_max']} - {filters['marca']} - {filters['ram']} - {filters['storage']} - {filters['processore']} -"
                   f"{filters['gpu']} - {filters['dimensione_schermo']} - {filters['display']} - {filters['battery_life']}")
        if not results.empty:
            message +=  "Ecco alcuni laptop che corrispondono ai tuoi criteri:\n"
            for _, r in results.sample(n=5).iterrows():
                message += (
                    f"- {r['name']} ({r['brand']}), CPU: {r['processor_name']}, "
                    f"RAM: {r['ram_gb']}GB, Prezzo: {r['price']}€\n"
                )
        else:
            message += "Non ho trovato laptop che corrispondono ai criteri forniti."

        dispatcher.utter_message(text=message)
        return []


class ActionMostraDettagli(Action):
    def name(self) -> str:
        return "action_mostra_dettagli"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        modello = tracker.get_slot("modello")

        if modello:
            match = df[df["name"].str.lower().str.contains(modello.lower())]
            if not match.empty:
                r = match.iloc[0]
                details = (
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
                dispatcher.utter_message(text=details)
            else:
                dispatcher.utter_message(text="Non ho trovato il modello indicato.")
        else:
            dispatcher.utter_message(text="Per favore specifica un modello.")

        return []


class ActionSalvaPreferito(Action):
    def name(self) -> str:
        return "action_salva_preferito"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        user_id = tracker.sender_id
        modello = tracker.get_slot("modello")

        if modello:
            user_favorites.setdefault(user_id, set()).add(modello)
            dispatcher.utter_message(text=f"{modello} è stato aggiunto ai preferiti.")
        else:
            dispatcher.utter_message(text="Non ho capito quale modello salvare.")

        return []


class ActionRimuoviPreferito(Action):
    def name(self) -> str:
        return "action_rimuovi_preferito"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        user_id = tracker.sender_id
        modello = tracker.get_slot("modello")

        if modello and user_id in user_favorites and modello in user_favorites[user_id]:
            user_favorites[user_id].remove(modello)
            dispatcher.utter_message(text=f"{modello} è stato rimosso dai preferiti.")
        else:
            dispatcher.utter_message(text="Modello non trovato nei preferiti.")

        return []


class ActionMostraPreferiti(Action):
    def name(self) -> str:
        return "action_mostra_preferiti"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        user_id = tracker.sender_id
        preferiti = user_favorites.get(user_id, [])

        if preferiti:
            dispatcher.utter_message(text="Ecco i tuoi preferiti:\n- " + "\n- ".join(preferiti))
        else:
            dispatcher.utter_message(text="Non hai ancora salvato nessun laptop tra i preferiti.")

        return []


class ActionConfermaAcquisto(Action):
    def name(self) -> str:
        return "action_conferma_acquisto"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        dispatcher.utter_message(text="Ottimo! Procediamo con l’acquisto. Riceverai i dettagli via email.")
        return []


class ActionAnnullaOperazione(Action):
    def name(self) -> str:
        return "action_annulla_operazione"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        dispatcher.utter_message(text="Operazione annullata. Se vuoi fare altro, chiedimi pure!")
        return []

class ActionSvuotaSlot(Action):
    def name(self) -> str:
        return "action_svuota_slot"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        slots_da_svuotare = [
            "marca", "ram", "storage", "processore", "gpu",
            "dimensione_schermo", "display", "battery_life",
            "prezzo_min", "prezzo_max", "modello"
        ]

        dispatcher.utter_message(text="Tutti i criteri di ricerca sono stati azzerati.")

        return [SlotSet(slot, None) for slot in slots_da_svuotare]