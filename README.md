# PrenHotel

**PrenHotel** è un'applicazione web per la gestione delle prenotazioni di camere di un hotel. Sviluppata con **Streamlit**, permette di selezionare camere, giorni di prenotazione e generare riepiloghi in PDF o inviare richieste tramite WhatsApp.

---

## Funzionalità principali

- Login tramite parola chiave (gestita tramite **Streamlit Secrets**)
- Selezione di tipo di camera e uso (singolo/doppio)
- Visualizzazione calendario con prenotazioni già effettuate
- Selezione dei giorni con controllo di consecutività
- Generazione di PDF con riepilogo prenotazioni
- Invio dei dettagli della prenotazione via WhatsApp
- Reset dei campi per nuova prenotazione
- Salvataggio temporaneo delle prenotazioni in memoria (session state)

---

## Requisiti

- Python 3.10 o superiore
- Pacchetti Python:

```bash
pip install -r requirements.txt
