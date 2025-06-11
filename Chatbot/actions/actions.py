from typing import Any, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Simulazione di un "catalogo" di laptop
catalogo_laptop = [
    {
        "modello": "HP Envy",
        "marca": "HP",
        "prezzo": 999,
        "ram": "16 GB",
        "storage": "512 GB SSD",
        "processore": "i7",
        "gpu": "Intel Iris",
        "dimensione_schermo": "13.3",
        "display": "touch",
        "battery_life": "10 ore"
    },
    {
        "modello": "Lenovo IdeaPad 5",
        "marca": "Lenovo",
        "prezzo": 749,
        "ram": "8 GB",
        "storage": "256 GB SSD",
        "processore": "i5",
        "gpu": "Intel UHD",
        "dimensione_schermo": "15.6",
        "display": "opaco",
        "battery_life": "8 ore"
    },
    {
        "modello": "ASUS ZenBook",
        "marca": "ASUS",
        "prezzo": 1199,
        "ram": "16 GB",
        "storage": "1 TB SSD",
        "processore": "i7",
        "gpu": "NVIDIA MX450",
        "dimensione_schermo": "14",
        "display": "OLED",
        "battery_life": "12 ore"
    }
]

# Dizionario per memorizzare i preferiti degli utenti
user_favorites = {}

def match_laptop(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    for laptop in catalogo_laptop:
        match = True
        for key, value in filters.items():
            if value and key in laptop:
                if isinstance(value, (int, float)):
                    if key == "prezzo_max" and laptop["prezzo"] > value:
                        match = False
                    elif key == "prezzo_min" and laptop["prezzo"] < value:
                        match = False
                elif value.lower() not in str(laptop[key]).lower():
                    match = False
        if match:
            results.append(laptop)
    return results


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

        if results:
            message = "Ecco alcuni laptop che corrispondono ai tuoi criteri:\n"
            for r in results:
                message += f"- {r['modello']} ({r['marca']}), {r['ram']}, {r['processore']}, {r['prezzo']}€\n"
        else:
            message = "Non ho trovato laptop che corrispondono ai criteri forniti."

        dispatcher.utter_message(text=message)
        return []


class ActionMostraDettagli(Action):
    def name(self) -> str:
        return "action_mostra_dettagli"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[str, Any]) -> List[Dict[str, Any]]:

        modello = tracker.get_slot("modello")
        laptop = next((l for l in catalogo_laptop if modello and modello.lower() in l["modello"].lower()), None)

        if laptop:
            details = "\n".join([f"{k.capitalize()}: {v}" for k, v in laptop.items()])
            dispatcher.utter_message(text=f"Ecco i dettagli per {modello}:\n{details}")
        else:
            dispatcher.utter_message(text="Non ho trovato il modello indicato.")

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
