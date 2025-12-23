import streamlit as st
from gusregon import GUS
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import date
import io

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Generator BDO - Elite Waste", page_icon="♻️")

st.title("♻️ Generator Pełnomocnictw BDO")
st.markdown("### Elite Waste")
st.info("Wpisz NIP klienta poniżej. System obsługuje zarówno spółki (KRS) jak i JDG (CEIDG).")

# --- POBIERANIE KLUCZA ---
try:
    api_key = st.secrets["GUS_KEY"]
except Exception as e:
    st.error("⚠️ Błąd konfiguracji! Nie znaleziono klucza GUS_KEY w zakładce Secrets.")
    st.stop()

# --- INTELIGENTNE WYCIĄGANIE DANYCH ---
def wyciagnij_dane_smart(dane):
    """
    Funkcja mapuje nazwy pól z GUS na podstawie Twoich zrzutów ekranu.
    """
    # 1. NAZWA
    nazwa = dane.get('nazwa', '')
    
    # 2. REGON (GUS dla JDG wrzuca go do 'regon9')
    regon = dane.get('regon') or dane.get('regon9') or ""

    # 3. MIEJSCOWOŚĆ
    # Priorytet: adsiedzmiejscowosc_nazwa (to widać u Ciebie w JSON)
    miasto = (dane.get('adsiedzmiejscowosc_nazwa') 
              or dane.get('siedzibamiejscowosc_nazwa') 
              or dane.get('miejscowosc') 
              or "")
    
    # 4. ULICA
    # Priorytet: adsiedzulica_nazwa (u Ciebie: "ul. Rojna")
    ulica = (dane.get('adsiedzulica_nazwa') 
             or dane.get('siedzibaulica_nazwa') 
             or dane.get('ulica') 
             or "")
    
    # 5. NUMERY
    nr_domu = (dane.get('adsiedznumernieruchomosci') 
               or dane.get('nr_nieruchomosci') 
               or "")
    
    nr_lokalu = (dane.get('adsiedznumerlokalu') 
                 or dane.get('nr_lokalu') 
                 or "")
    
    # 6. KOD POCZTOWY
    kod = (dane.get('adsiedzkodpocztowy') 
           or dane.get('kod_pocztowy') 
           or "")

    # 7. WOJEWÓDZTWO
    woj = (dane.get('adsiedzwojewodztwo_nazwa') 
           or dane.get('wojewodztwo') 
           or "")

    return {
        'nazwa': nazwa,
        'miasto': miasto,
        'ulica': ulica,
        'nr_domu': nr_domu,
        'nr_lokalu': nr_lokalu,
        'kod': kod,
        'wojewodztwo': woj,
        'regon': regon
    }

# --- GENERATOR DOKUMENTU ---
def generuj_word(info, nip_raw):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)

    data_dzis = date.today().strftime("%d.%m.%Y")

    # Data
    p = doc.add_paragraph(f"Łódź, dnia {data_dzis} r.")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Mocodawca
    doc.add_paragraph("\nMocodawca").runs[0].bold = True
    
    # Budowanie adresu
    adres_string = ""
    ulica_czysta = info['ulica']
    
    if ulica_czysta:
        # Twoje dane mają już "ul." w nazwie (widzę to w JSON), więc nie dodajemy tego drugi raz
        adres_string += f"{ulica_czysta} {info['nr_domu']}"
    else:
        adres_string += f"{info['nr_domu']}" # Wioska bez ulicy
        
    if info['nr_lokalu']:
        adres_string += f"/{info['nr_lokalu']}"
    
    adres_string += f", {info['kod']} {info['miasto']}"

    # Wypisywanie danych w nagłówku
    doc.add_paragraph(info['nazwa'].upper()) 
    doc.add_paragraph(adres_string)
    doc.add_paragraph(f"NIP: {nip_raw}")
    doc.add_
