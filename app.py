import streamlit as st
from gusregon import GUS
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import date
import io

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Generator Pełnomocnictwa BDO", page_icon="📝")

st.title("📝 Generator Pełnomocnictw BDO")
st.markdown("""
To narzędzie przygotowane przez **Elite Waste**.
Wpisz swój **NIP**, a system automatycznie pobierze dane z GUS i przygotuje dokument do podpisu.
""")

# --- POBIERANIE KLUCZA Z SEKRETÓW ---
# Klucz będzie bezpiecznie ukryty w ustawieniach strony (instrukcja niżej)
api_key = st.secrets["GUS_KEY"]

nip_input = st.text_input("Podaj NIP (bez kresek):", max_chars=10)

def generuj_dokument(dane_firmy, nip):
    # Tworzenie dokumentu w pamięci (bez zapisywania na dysku)
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)

    data_dzis = date.today().strftime("%d.%m.%Y")
    
    # Nagłówek
    p = doc.add_paragraph(f"Łódź, dnia {data_dzis} r.")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    doc.add_paragraph("\nMocodawca").runs[0].bold = True
    doc.add_paragraph(f"{dane_firmy['nazwa']}")
    
    adres_caly = f"{dane_firmy['ulica']} {dane_firmy['nr_nieruchomosci']}"
    if dane_firmy['nr_lokalu']: adres_caly += f"/{dane_firmy['nr_lokalu']}"
    adres_caly += f", {dane_firmy['kod_pocztowy']} {dane_firmy['miejscowosc']}"
    
    doc.add_paragraph(adres_caly)
    doc.add_paragraph(f"NIP: {nip}")
    doc.add_paragraph(f"REGON: {dane_firmy['regon']}")

    # Tytuł
    tytul = doc.add_paragraph("\nPEŁNOMOCNICTWO")
    tytul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tytul.runs[0].bold = True
    tytul.runs[0].font.size = Pt(14)

    # Treść
    woj = dane_firmy['wojewodztwo'].lower()
    # Prosta odmiana województwa (można rozbudować)
    mapa_woj = {
        'łódzkie': 'Łódzkiego', 'mazowieckie': 'Mazowieckiego', 'wielkopolskie': 'Wielkopolskiego',
        'małopolskie': 'Małopolskiego', 'śląskie': 'Śląskiego', 'pomorskie': 'Pomorskiego',
        'dolnośląskie': 'Dolnośląskiego', 'podkarpackie': 'Podkarpackiego', 'lubelskie': 'Lubelskiego',
        'kujawsko-pomorskie': 'Kujawsko-Pomorskiego', 'zachodniopomorskie': 'Zachodniopomorskiego',
        'warmińsko-mazurskie': 'Warmińsko-Mazurskiego', 'świętokrzyskie': 'Świętokrzyskiego',
        'podlaskie': 'Podlaskiego', 'opolskie': 'Opolskiego', 'lubuskie': 'Lubuskiego'
    }
    nazwa_woj = mapa_woj.get(woj, woj.capitalize())

    tekst = (
        f"Działając w imieniu {dane_firmy['nazwa']} z siedzibą w {dane_firmy['miejscowosc']}, "
        f"{adres_caly}, posiadając prawo reprezentacji tego podmiotu w zakresie ustanawiania pełnomocnictw, "
        f"upoważniam Pana Pawła Bolimowskiego oraz Pana Patryka Kosteckiego do samodzielnej reprezentacji "
        f"{dane_firmy['nazwa']} przed Urzędem Marszałkowskim Województwa {nazwa_woj} "
        f"w sprawach BDO."
    )
    p_main = doc.add_paragraph(tekst)
    p_main.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Lista czynności
    punkty = [
        "złożenia wniosku o wpis do rejestru (art. 50 ustawy o odpadach);",
        "wyznaczania upoważnionych użytkowników (art. 79 ust. 7);",
        "zmiany wpisu w rejestrze (art. 59);",
        "wykreślenia z rejestru (art. 60);",
        "prowadzenia ewidencji odpadów (art. 66 i nast.);",
        "prowadzenia sprawozdawczości (art. 73 i nast.)."
    ]
    for punkt in punkty:
        p = doc.add_paragraph(f"- {punkt}")
        p.paragraph_format.left_indent = Cm(1)

    doc.add_paragraph(f"\nPełnomocnictwo ważne od {data_dzis} r. do odwołania.")
    doc.add_paragraph("\n\n..................................................................")
    doc.add_paragraph("(Czytelny podpis oraz pieczątka Mocodawcy)")

    # Zapis do bufora pamięci (żeby można było pobrać)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

if st.button("🔍 Szukaj firmy i generuj"):
    if not nip_input:
        st.warning("Wpisz NIP!")
    else:
        try:
            gus = GUS(api_key=api_key)
            dane = gus.search(nip=nip_input)
            
            st.success(f"Znaleziono: **{dane['nazwa']}**")
            st.info(f"Adres: {dane['ulica']} {dane['nr_nieruchomosci']}, {dane['miejscowosc']}")
            
            # Generowanie pliku
            plik_word = generuj_dokument(dane, nip_input)
            
            st.markdown("### 👇 Pobierz gotowy dokument:")
            st.download_button(
                label="📥 POBIERZ PEŁNOMOCNICTWO (DOCX)",
                data=plik_word,
                file_name=f"Pelnomocnictwo_BDO_{nip_input}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.info("Pamiętaj: Wydrukuj, podpisz i odeślij skan do nas!")
            
        except Exception as e:
            st.error(f"Nie znaleziono firmy lub błąd GUS. Sprawdź NIP. ({e})")
