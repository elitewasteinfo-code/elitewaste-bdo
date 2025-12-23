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
    Funkcja mapuje dziwne nazwy pól z GUS (widoczne na zrzutach ekranu) na nasze standardowe.
    """
    # 1. NAZWA
    nazwa = dane.get('nazwa', '')
    
    # 2. REGON (GUS dla JDG wrzuca go do 'regon9')
    regon = dane.get('regon') or dane.get('regon9') or ""

    # 3. MIEJSCOWOŚĆ
    # Szukamy: standardowo LUB adsiedz... LUB siedziba...
    miasto = (dane.get('miejscowosc') 
              or dane.get('adsiedzmiejscowosc_nazwa') 
              or dane.get('siedzibamiejscowosc_nazwa') 
              or "")
    
    # 4. ULICA
    ulica = (dane.get('ulica') 
             or dane.get('adsiedzulica_nazwa') 
             or dane.get('siedzibaulica_nazwa') 
             or "")
    
    # 5. NUMERY
    nr_domu = (dane.get('nr_nieruchomosci') 
               or dane.get('adsiedznumernieruchomosci') 
               or "")
    
    nr_lokalu = (dane.get('nr_lokalu') 
                 or dane.get('adsiedznumerlokalu') 
                 or "")
    
    # 6. KOD POCZTOWY
    kod = (dane.get('kod_pocztowy') 
           or dane.get('adsiedzkodpocztowy') 
           or "")

    # 7. WOJEWÓDZTWO
    woj = (dane.get('wojewodztwo') 
           or dane.get('adsiedzwojewodztwo_nazwa') 
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
    
    # Budowanie adresu (Logika: czy ulica zawiera już "ul."?)
    adres_string = ""
    ulica_czysta = info['ulica']
    
    if ulica_czysta:
        # Sprawdzamy czy GUS zwrócił już "ul. Rojna" czy samą "Rojna"
        if "ul." in ulica_czysta.lower():
            adres_string += f"{ulica_czysta} {info['nr_domu']}"
        else:
            adres_string += f"ul. {ulica_czysta} {info['nr_domu']}"
    else:
        adres_string += f"{info['nr_domu']}" # Wioska bez ulicy
        
    if info['nr_lokalu']:
        adres_string += f"/{info['nr_lokalu']}"
    
    adres_string += f", {info['kod']} {info['miasto']}"

    # Wypisywanie danych w nagłówku
    doc.add_paragraph(info['nazwa'].upper()) 
    doc.add_paragraph(adres_string)
    doc.add_paragraph(f"NIP: {nip_raw}")
    doc.add_paragraph(f"REGON: {info['regon']}")

    # Tytuł
    tytul = doc.add_paragraph("\nPEŁNOMOCNICTWO")
    tytul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tytul.runs[0].bold = True
    tytul.runs[0].font.size = Pt(14)

    # Województwo - obsługa odmiany
    woj_text = info['wojewodztwo'].lower()
    mapa_woj = {
        'łódzkie': 'Łódzkiego', 'mazowieckie': 'Mazowieckiego', 'wielkopolskie': 'Wielkopolskiego',
        'małopolskie': 'Małopolskiego', 'śląskie': 'Śląskiego', 'pomorskie': 'Pomorskiego',
        'dolnośląskie': 'Dolnośląskiego', 'podkarpackie': 'Podkarpackiego', 'lubelskie': 'Lubelskiego',
        'kujawsko-pomorskie': 'Kujawsko-Pomorskiego', 'zachodniopomorskie': 'Zachodniopomorskiego',
        'warmińsko-mazurskie': 'Warmińsko-Mazurskiego', 'świętokrzyskie': 'Świętokrzyskiego',
        'podlaskie': 'Podlaskiego', 'opolskie': 'Opolskiego', 'lubuskie': 'Lubuskiego'
    }
    
    # Próba dopasowania odmiany, jeśli nie ma - wstawia oryginał
    urzad_wojewodztwo = mapa_woj.get(woj_text, woj_text.capitalize())
    
    if not urzad_wojewodztwo:
         urzad_wojewodztwo = "........................................"

    # Treść
    tekst = (
        f"Działając w imieniu {info['nazwa']} z siedzibą w {info['miasto']}, "
        f"{adres_string}, posiadając prawo reprezentacji tego podmiotu w zakresie ustanawiania pełnomocnictw, "
        f"upoważniam Pana Pawła Bolimowskiego oraz Pana Patryka Kosteckiego do samodzielnej reprezentacji "
        f"{info['nazwa']} przed Urzędem Marszałkowskim Województwa {urzad_wojewodztwo} "
        f"w następujących sprawach załatwianych za pośrednictwem indywidualnego konta "
        f"w Bazie danych o produktach i opakowaniach oraz o gospodarce odpadami
