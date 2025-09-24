import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date, timedelta
from urllib.parse import quote
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# --- Configurazioni pagina ---
st.set_page_config(page_title="PrenHotel", layout="wide")

# --- CSS aggiornato ---
st.markdown("""
<style>
  [data-testid="stSidebar"] { 
      background-color: #f4f7fb; 
      color: #003366; 
      width: 33% !important; 
      min-width: 250px;
  }
  [data-testid="stSidebar"] * { color: #003366 !important; }
  .block-container { padding: 1rem 2rem; width: 67% !important; }
  .app-title { font-size: 36px; font-weight: 700; color: #003366; font-family: 'Helvetica', 'Arial', sans-serif; margin-top:20px; margin-bottom: 1rem; text-align:center; }
  .calendar-title { font-size:20px; font-weight:700; color:#ff6600; text-align:center; margin-top:10px; margin-bottom:10px; }
  .calendar-cell { width:100%; padding:8px; border-radius:10px; box-sizing:border-box; margin-bottom:4px; }
  .day-normal { background:#e6f3ff; }
  .day-holiday { background:#ffe6f0; }
  .day-selected { background:#c7f0d4; border:2px solid #2ecc71; }
  .day-booked { background:#ff6b6b; color:white; }
  .day-number { font-weight:700; font-size:16px; }
  .day-mark { font-size:13px; color:green; margin-top:4px; }
  .nav-button { border:none; background:none; font-size:20px; }
</style>
""", unsafe_allow_html=True)

# --- Titolo principale ---
st.markdown('<div class="app-title">PrenHotel</div>', unsafe_allow_html=True)

import streamlit as st

# --- Carico password da secrets ---
ACCESS_KEY = st.secrets["credentials"]["access_key"]

if "access_granted" not in st.session_state:
    st.session_state.access_granted = False

if not st.session_state.access_granted:
    user_input = st.text_input("Inserisci la parola chiave per accedere", type="password")
    if st.button("Accedi"):
        if user_input == ACCESS_KEY:
            st.session_state.access_granted = True
            st.rerun()
        else:
            st.error("Parola chiave errata!")
    st.stop()


# --- Prezzi e camere ---
PREZZI = {
    "alta": {"matrimoniale": 90, "doppia": 90, "doppia_uso_singolo": 75, "singola": 67},
    "bassa": {"matrimoniale": 80, "doppia": 80, "doppia_uso_singolo": 65, "singola": 57},
}
CAMERE = {
    "Primo Piano": {"doppie":["107","106","105","104","101","103"], "quadruple":["109"], "matrimoniale":["109"], "singole":["102"]},
    "Secondo Piano": {"singole":["202"], "matrimoniale":["209"], "doppie":["207","204","203","201"], "quadruple":["205","208"]},
}
TIPO_TO_KEY = {"singola": "singole", "doppia": "doppie", "matrimoniale": "matrimoniale", "quadruple": "quadruple"}

# --- Session state inizializzazione ---
for key in ["prenotazioni","selezionate","current_month","current_year","holidays",
            "s_azienda","s_dipendente","s_dipendente2","s_tipo","s_uso","s_camera",
            "s_telefono","s_note","reset_fields"]:
    if key not in st.session_state:
        if key=="current_month": st.session_state[key]=datetime.today().month
        elif key=="current_year": st.session_state[key]=2025
        elif key=="s_tipo": st.session_state[key]="singola"
        elif key=="s_uso": st.session_state[key]="singolo"
        elif key=="s_camera": st.session_state[key]=""
        elif key in ["prenotazioni","selezionate"]: st.session_state[key]=[]
        elif key=="holidays": st.session_state[key]=set()
        elif key=="reset_fields": st.session_state[key]=False
        else: st.session_state[key]=""

# --- Funzioni ---
def parse_date(s): return datetime.strptime(s,"%d/%m/%Y").date()

def get_booked_dates():
    booked=set()
    for p in st.session_state.prenotazioni:
        try:
            d0=parse_date(p[3])
            n=int(p[4])
            for i in range(n):
                booked.add(d0+timedelta(days=i))
        except:
            continue
    return booked

def bookings_for_day(d):
    hits=[]
    for idx,p in enumerate(st.session_state.prenotazioni):
        try:
            d0=parse_date(p[3])
            n=int(p[4])
            if d0<=d<d0+timedelta(days=n):
                hits.append((idx,p))
        except:
            continue
    return hits

def is_consecutive(dates):
    if not dates: return True
    ds=sorted(dates)
    for a,b in zip(ds,ds[1:]):
        if (b-a).days!=1: return False
    return True

def calcola_prezzo_per_notti(tipo,uso,dates):
    totale=0
    for d in dates:
        key="doppia_uso_singolo" if(tipo=="doppia" and uso=="singolo") else tipo
        alta=date(d.year,5,9)<d<=date(d.year,9,7)
        stagione="alta" if alta else "bassa"
        totale+=PREZZI[stagione][key]
    return totale

def calcola_totale_prenotazioni():
    # totale può essere float o int a seconda calcolo; usiamo float-safe
    return sum(float(p[8]) for p in st.session_state.prenotazioni)

def genera_pdf_prenotazioni():
    buffer=BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=A4)
    elements=[]
    styles=getSampleStyleSheet()
    timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    elements.append(Paragraph(f"Riepilogo Prenotazioni - {timestamp}",styles['Title']))
    elements.append(Spacer(1,12))
    data=[["Azienda","Dipendente","Dipendente 2","Check-in","Notti","Tipo","Camera","Uso","Totale €","Telefono","Note"]]
    for p in st.session_state.prenotazioni:
        data.append([p[0],p[1],p[2],p[3],str(p[4]),p[5],p[6],p[7],f"€{p[8]}",p[9],p[10]])
    table=Table(data,repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID',(0,0),(-1,-1),0.5,colors.grey),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('ALIGN',(4,1),(4,-1),'CENTER'),
        ('ALIGN',(8,1),(8,-1),'RIGHT')
    ]))
    elements.append(table)
    elements.append(Spacer(1,12))
    totale=calcola_totale_prenotazioni()
    elements.append(Paragraph(f"Totale prenotazioni: €{totale}",styles['Heading2']))
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- Sidebar ---
with st.sidebar:
    # valori che tengono conto del reset_fields flag
    s_azienda_val = "" if st.session_state.reset_fields else st.session_state.s_azienda
    s_dipendente_val = "" if st.session_state.reset_fields else st.session_state.s_dipendente
    s_dipendente2_val = "" if st.session_state.reset_fields else st.session_state.s_dipendente2
    s_telefono_val = "" if st.session_state.reset_fields else st.session_state.s_telefono
    s_note_val = "" if st.session_state.reset_fields else st.session_state.s_note
    s_tipo_val = "singola" if st.session_state.reset_fields else st.session_state.s_tipo
    s_uso_val = "singolo" if st.session_state.reset_fields else st.session_state.s_uso
    s_camera_val = "" if st.session_state.reset_fields else st.session_state.s_camera

    st.text_input("Nome Azienda", key="s_azienda", value=s_azienda_val)
    st.text_input("Nome Dipendente", key="s_dipendente", value=s_dipendente_val)
    st.text_input("Numero di telefono", key="s_telefono", value=s_telefono_val)
    st.selectbox("Tipo Camera", ["singola","doppia","matrimoniale","quadruple"], key="s_tipo",
                 index=["singola","doppia","matrimoniale","quadruple"].index(s_tipo_val))
    st.selectbox("Uso", ["singolo","doppio"], key="s_uso", index=["singolo","doppio"].index(s_uso_val))

    if st.session_state.s_uso=="doppio":
        st.text_input("Dipendente 2 (facoltativo)", key="s_dipendente2", value=s_dipendente2_val)

    st.text_area("Richieste e segnalazioni", key="s_note", value=s_note_val, height=60)

    key_tipo=TIPO_TO_KEY.get(st.session_state.s_tipo,st.session_state.s_tipo)
    camere_list=[]
    for piano in CAMERE.values():
        camere_list.extend(piano.get(key_tipo,[]))
    if not camere_list:
        camere_list=["Nessuna camera disponibile"]
    # safe index
    sel_index = 0
    if st.session_state.s_camera!="" and st.session_state.s_camera in camere_list:
        sel_index = camere_list.index(st.session_state.s_camera)
    st.selectbox("Camera", camere_list, key="s_camera", index=sel_index)

    st.markdown("---")
    c1,c2=st.columns(2)
    with c1:
        if st.button("🆕 Nuova prenotazione"):
            for key in ["s_azienda","s_dipendente","s_dipendente2","s_telefono","s_note","s_tipo","s_uso","s_camera"]:
                st.session_state[key] = "" if key not in ["s_tipo","s_uso"] else ("singola" if key=="s_tipo" else "singolo")
            st.session_state.selezionate = []
            st.rerun()

    with c2:
        if st.button("Prenota"):
            if not st.session_state.s_azienda or not st.session_state.s_dipendente or not st.session_state.selezionate or st.session_state.s_camera=="Nessuna camera disponibile":
                st.warning("Compila tutti i campi obbligatori e seleziona almeno un giorno.")
            elif not is_consecutive(st.session_state.selezionate):
                st.error("I giorni selezionati devono essere consecutivi.")
            else:
                conflicts=[]
                for d in st.session_state.selezionate:
                    hits=bookings_for_day(d)
                    for _,p in hits:
                        if p[6]==st.session_state.s_camera:
                            conflicts.append(d.strftime("%d/%m/%Y"))
                if conflicts:
                    st.error(f"Conflitto: la camera {st.session_state.s_camera} è già prenotata in: {', '.join(conflicts)}")
                else:
                    n=len(st.session_state.selezionate)
                    start=min(st.session_state.selezionate)
                    total=calcola_prezzo_per_notti(st.session_state.s_tipo,st.session_state.s_uso,sorted(st.session_state.selezionate))
                    st.session_state.prenotazioni.append([
                        st.session_state.s_azienda,
                        st.session_state.s_dipendente,
                        st.session_state.s_dipendente2,
                        start.strftime("%d/%m/%Y"),
                        n,
                        st.session_state.s_tipo,
                        st.session_state.s_camera,
                        st.session_state.s_uso,
                        total,
                        st.session_state.s_telefono,
                        st.session_state.s_note
                    ])
                    st.success(f"Prenotazione registrata. Totale: €{total}")
                    st.session_state.selezionate=[]

    # dopo il rerun dovremmo riportare reset_fields a False se è True
    # ma non farlo qui in modo da non annullare prima che i widget leggano il flag.
    # lo impostiamo a False all'inizio della prossima esecuzione:
    if st.session_state.reset_fields:
        st.session_state.reset_fields = False

    # Tabella prenotazioni e controlli
    if st.session_state.prenotazioni:
        dfp=pd.DataFrame(st.session_state.prenotazioni,columns=[
            "Azienda","Dipendente","Dipendente 2","Check-in","Notti","Tipo","Camera","Uso","Totale €","Telefono","Note"])
        st.dataframe(dfp,use_container_width=True)
        idx_to_remove=st.number_input("Elimina record (indice)",min_value=0,max_value=len(dfp)-1,step=1)
        if st.button("Elimina record selezionato"):
            st.session_state.prenotazioni.pop(int(idx_to_remove))
            st.success(f"Record {int(idx_to_remove)} eliminato.")

        pdf_buffer=genera_pdf_prenotazioni()
        st.download_button("Riepilogo PDF", data=pdf_buffer, file_name="richiesta_preno.pdf", mime="application/pdf")

        totale=calcola_totale_prenotazioni()
        riepilogo="\n".join([f"{p[0]} {p[1]} {p[2]} {p[3]} - {p[4]}n - €{p[8]}" for p in st.session_state.prenotazioni])
        messaggio=f"Richiesta di prenotazione:\n{riepilogo}\nTotale: €{totale}"
        link_whatsapp=f"https://wa.me/?text={quote(messaggio)}"
        st.markdown(f"[Invia richiesta con WhatsApp]({link_whatsapp})",unsafe_allow_html=True)

# --- Main: Calendario (mostra celle con checkbox) ---
mese=st.session_state.current_month
anno=st.session_state.current_year

cal=calendar.Calendar(firstweekday=0)
days_matrix=cal.monthdatescalendar(anno,mese)
booked=get_booked_dates()

for settimana in days_matrix:
    cols=st.columns(7)
    for i,d in enumerate(settimana):
        col=cols[i]
        if d.month!=mese:
            col.markdown("<div style='padding:12px; color:#bbb'></div>",unsafe_allow_html=True)
            continue
        is_holiday=(d.strftime("%d/%m/%Y") in st.session_state.holidays) or (d.weekday()==6)
        is_selected=d in st.session_state.selezionate
        is_booked=d in booked
        classes="calendar-cell "+("day-holiday" if is_holiday else "day-normal")
        if is_selected: classes="calendar-cell day-selected"
        if is_booked: classes="calendar-cell day-booked"
        hits=bookings_for_day(d)
        tooltip="".join([f"{p[1]} ({p[6]}) - {p[4]}n\\n" for _,p in hits])
        tooltip_attr=f"title='{tooltip}'" if tooltip else ""
        mark_html="<div class='day-mark'>X</div>" if is_selected or is_booked else ""
        col.markdown(f"<div class='{classes}' {tooltip_attr}><div class='day-number'>{d.day}</div>{mark_html}</div>",unsafe_allow_html=True)

        # Checkbox per selezione senza rerun
        key_chk=f"sel_{d.isoformat()}"
        checked=d in st.session_state.selezionate
        new_val=col.checkbox("",value=checked,key=key_chk)
        if new_val!=checked:
            if new_val: st.session_state.selezionate.append(d)
            else: st.session_state.selezionate.remove(d)

# Titolo mese ridotto (una sola volta, sopra le frecce)
st.markdown(f"<div class='calendar-title'>{calendar.month_name[mese]} {anno}</div>",unsafe_allow_html=True)

# Pulsanti freccia sotto calendario
c1,c2,c3=st.columns([1,6,1])
with c1:
    if st.button("⬅️",key="prev"):
        st.session_state.current_month-=1
        if st.session_state.current_month<1:
            st.session_state.current_month=12
            st.session_state.current_year-=1
        st.rerun()
with c3:
    if st.button("➡️",key="next"):
        st.session_state.current_month+=1
        if st.session_state.current_month>12:
            st.session_state.current_month=1
            st.session_state.current_year+=1
        st.rerun()
