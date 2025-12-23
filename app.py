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
st.info("Wpisz NIP klienta poniżej. System pobierze dane z GUS i wygeneruje gotowy dokument.")

# --- POBIERANIE KLUCZA Z SEKRETÓW ---
try:
    api_key = st.secrets["GUS_KEY"]
except Exception as e:
    st.error("⚠️ Błąd konfiguracji! Nie znaleziono klucza GUS_KEY w zakładce Secrets.")
    st.stop()

# --- INTERFEJS ---
nip_input = st.text_input("Podaj NIP (sam numer, bez kresek):", max_chars=10)

# --- FUNKCJA POMOCNICZA DO ADRESU ---
def bezpieczny_adres(dane):
    """Tworzy ładny string adresu niezależnie od tego, czy firma ma ulicę czy nie."""
    ulica = dane.get('ulica', '') # Jeśli brak, wstaw pusty tekst
    nr_domu = dane.get('nr_nieruchomosci', '')
    nr_lokalu = dane.get('nr_lokalu', '')
    kod = dane.get('kod_pocztowy', '')
    miasto = dane.get('miejscowosc', '')
    
    adres_linia = ""
    if ulica:
        adres_linia += f"ul. {ulica} {nr_domu}"
    else:
        adres_linia += f"{nr_domu}" # Np. dla wsi bez ulic
        
    if nr_lokalu:
        adres_linia += f"/{nr_lokalu}"
        
    adres_linia += f", {kod} {miasto}"
    return adres_linia

# --- FUNKCJA GENERUJĄCA DOKUMENT ---
def generuj_word(dane, nip):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Times New Roman'
    style.font.size = Pt(11)

    data_dzis = date.today().strftime("%d.%m.%Y")

    # Miejscowość i data
    p = doc.add_paragraph(f"Łódź, dnia {data_dzis} r.")
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Mocodawca
    doc.add_paragraph("\nMocodawca").runs[0].bold = True
    doc.add_paragraph(f"{dane.get('nazwa', 'Brak nazwy')}")
    
    # Budowanie adresu bezpieczną metodą
    adres_caly = bezpieczny_adres(dane)
    miejscowosc_firmy = dane.get('miejscowosc', '')

    doc.add_paragraph(adres_caly)
    doc.add_paragraph(f"NIP: {nip}")
    doc.add_paragraph(f"REGON: {dane.get('regon', '')}")

    # Tytuł
    tytul = doc.add_paragraph("\nPEŁNOMOCNICTWO")
    tytul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tytul.runs[0].bold = True
    tytul.runs[0].font.size = Pt(14)

    # Ustalanie województwa
    woj_raw = dane.get('wojewodztwo', '').lower()
    mapa_woj = {
        'łódzkie': 'Łódzkiego', 'mazowieckie': 'Mazowieckiego', 'wielkopolskie': 'Wielkopolskiego',
        'małopolskie': 'Małopolskiego', 'śląskie': 'Śląskiego', 'pomorskie': 'Pomorskiego',
        'dolnośląskie': 'Dolnośląskiego', 'podkarpackie': 'Podkarpackiego', 'lubelskie': 'Lubelskiego',
        'kujawsko-pomorskie': 'Kujawsko-Pomorskiego', 'zachodniopomorskie': 'Zachodniopomorskiego',
        'warmińsko-mazurskie': 'Warmińsko-Mazurskiego', 'świętokrzyskie': 'Świętokrzyskiego',
        'podlaskie': 'Podlaskiego', 'opolskie': 'Opolskiego', 'lubuskie': 'Lubuskiego'
    }
    # Domyślnie puste, jeśli brak danych
    urzad_wojewodztwo = mapa_woj.get(woj_raw, "....................") 

    # Treść główna
    tekst = (
        f"Działając w imieniu {dane.get('nazwa', '')} z siedzibą w {miejscowosc_firmy}, "
        f"{adres_caly}, posiadając prawo reprezentacji tego podmiotu w zakresie ustanawiania pełnomocnictw, "
        f"upoważniam Pana Pawła Bolimowskiego oraz Pana Patryka Kosteckiego do samodzielnej reprezentacji "
        f"{dane.get('nazwa', '')} przed Urzędem Marszałkowskim Województwa {urzad_wojewodztwo} "
        f"w następujących sprawach załatwianych za pośrednictwem indywidualnego konta "
        f"w Bazie danych o produktach i opakowaniach oraz o gospodarce odpadami (BDO):\n"
    )
    p_main = doc.add_paragraph(tekst)
    p_main.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Punkty
    punkty = [
        "złożenia wniosku o wpis do rejestru na wniosek zgodnie z art. 50 ustawy o odpadach;",
        "wyznaczania upoważnionych użytkowników zgodnie z art. 79 ust. 7 ustawy o odpadach;",
        "złożenia wniosku o zmianę wpisu w rejestrze zgodnie z art. 59 ustawy o odpadach;",
        "złożenia wniosku o wykreślenie z rejestru zgodnie z art. 60 ustawy o odpadach;",
        "prowadzenia ewidencji odpadów zgodnie z art. 66 i nast. ustawy o odpadach;",
        "prowadzenia sprawozdawczości zgodnie z art. 73 i nast. ustawy o odpadach."
    ]
    for punkt in punkty:
        p = doc.add_paragraph(f"- {punkt}")
        p.paragraph_format.left_indent = Cm(1)

    # Stopka
    doc.add_paragraph(f"\nPełnomocnictwo ustanawia się od dnia {data_dzis} r. do odwołania.")
    doc.add_paragraph(
        "Odwołanie pełnomocnictwa nie powoduje unieważnienia czynności wykonanych przez upoważnioną osobę "
        "ani konsekwencji tych czynności, jeżeli czynność miała miejsce przed poinformowaniem organu właściwego o cofnięciu pełnomocnictwa."
    )
    doc.add_paragraph("\n\n..................................................................")
    doc.add_paragraph("(Czytelny podpis oraz pieczątka Mocodawcy)")

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- LOGIKA APLIKACJI ---
if st.button("🔍 Znajdź firmę i generuj dokument"):
    if not nip_input:
        st.warning("Proszę wpisać NIP.")
    else:
        try:
            # Połączenie z GUS
            gus = GUS(api_key=api_key)
            dane_firmy = gus.search(nip=nip_input)
            
            st.success(f"Znaleziono firmę: {dane_firmy.get('nazwa', 'Nazwa niedostępna')}")
            
            # Generowanie pliku
            plik_word = generuj_word(dane_firmy, nip_input)
            
            st.markdown("### 👇 Pobierz gotowy plik:")
            st.download_button(
                label="📥 POBIERZ PEŁNOMOCNICTWO (DOCX)",
                data=plik_word,
                file_name=f"Pelnomocnictwo_BDO_{nip_input}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        except Exception as e:
            st.error(f"Wystąpił błąd. (Szczegóły: {e})")
