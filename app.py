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
st.info("Wpisz NIP klienta poniżej. System sprawdzi różne formaty danych w GUS.")

# --- POBIERANIE KLUCZA ---
try:
    api_key = st.secrets["GUS_KEY"]
except Exception as e:
    st.error("⚠️ Błąd konfiguracji! Nie znaleziono klucza GUS_KEY w zakładce Secrets.")
    st.stop()

# --- FUNKCJA NAPRAWCZA DO DANYCH (Mocne mapowanie) ---
def wyciagnij_dane_smart(dane):
    """
    Funkcja szuka danych w różnych polach, bo GUS inaczej nazywa pola dla JDG a inaczej dla Spółek.
    """
    # 1. NAZWA
    nazwa = dane.get('nazwa', '')
    if not nazwa:
        # Czasem nazwa jest rozbita na imię i nazwisko w JDG
        imie = dane.get('imie1', '')
        nazwisko = dane.get('nazwisko', '')
        if imie and nazwisko:
            nazwa = f"{imie} {nazwisko}"

    # 2. MIEJSCOWOŚĆ (Szukamy w 3 miejscach)
    miasto = dane.get('miejscowosc') or dane.get('adsiedzmiejscowosc') or dane.get('siedzibamiejscowosc') or ""
    
    # 3. ULICA (Szukamy w 3 miejscach)
    ulica = dane.get('ulica') or dane.get('adsiedzulica') or dane.get('siedzibaulica') or ""
    
    # 4. NUMERY DOMU/LOKALU
    nr_domu = dane.get('nr_nieruchomosci') or dane.get('adsiedznrnieruchomosci') or ""
    nr_lokalu = dane.get('nr_lokalu') or dane.get('adsiedznrlokalu') or ""
    
    # 5. KOD POCZTOWY
    kod = dane.get('kod_pocztowy') or dane.get('adsiedzkodpocztowy') or ""

    # 6. WOJEWÓDZTWO
    woj = dane.get('wojewodztwo') or dane.get('adsiedzwojewodztwo') or ""

    # 7. REGON (Musi być)
    regon = dane.get('regon') or ""

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
    if info['ulica']:
        adres_string += f"ul. {info['ulica']} {info['nr_domu']}"
    else:
        adres_string += f"{info['nr_domu']}" # Wioska bez ulicy
        
    if info['nr_lokalu']:
        adres_string += f"/{info['nr_lokalu']}"
    
    adres_string += f", {info['kod']} {info['miasto']}"

    # Wypisywanie danych w nagłówku
    doc.add_paragraph(info['nazwa'].upper()) # Nazwa dużymi literami
    doc.add_paragraph(adres_string)
    doc.add_paragraph(f"NIP: {nip_raw}")
    doc.add_paragraph(f"REGON: {info['regon']}")

    # Tytuł
    tytul = doc.add_paragraph("\nPEŁNOMOCNICTWO")
    tytul.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tytul.runs[0].bold = True
    tytul.runs[0].font.size = Pt(14)

    # Województwo - obsługa braku danych
    woj_text = info['wojewodztwo'].lower()
    mapa_woj = {
        'łódzkie': 'Łódzkiego', 'mazowieckie': 'Mazowieckiego', 'wielkopolskie': 'Wielkopolskiego',
        'małopolskie': 'Małopolskiego', 'śląskie': 'Śląskiego', 'pomorskie': 'Pomorskiego',
        'dolnośląskie': 'Dolnośląskiego', 'podkarpackie': 'Podkarpackiego', 'lubelskie': 'Lubelskiego',
        'kujawsko-pomorskie': 'Kujawsko-Pomorskiego', 'zachodniopomorskie': 'Zachodniopomorskiego',
        'warmińsko-mazurskie': 'Warmińsko-Mazurskiego', 'świętokrzyskie': 'Świętokrzyskiego',
        'podlaskie': 'Podlaskiego', 'opolskie': 'Opolskiego', 'lubuskie': 'Lubuskiego'
    }
    
    if woj_text:
        urzad_wojewodztwo = mapa_woj.get(woj_text, woj_text.capitalize())
    else:
        urzad_wojewodztwo = "........................................"

    # Treść
    tekst = (
        f"Działając w imieniu {info['nazwa']} z siedzibą w {info['miasto']}, "
        f"{adres_string}, posiadając prawo reprezentacji tego podmiotu w zakresie ustanawiania pełnomocnictw, "
        f"upoważniam Pana Pawła Bolimowskiego oraz Pana Patryka Kosteckiego do samodzielnej reprezentacji "
        f"{info['nazwa']} przed Urzędem Marszałkowskim Województwa {urzad_wojewodztwo} "
        f"w następujących sprawach załatwianych za pośrednictwem indywidualnego konta "
        f"w Bazie danych o produktach i opakowaniach oraz o gospodarce odpadami (BDO):\n"
    )
    p_main = doc.add_paragraph(tekst)
    p_main.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Lista czynności
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
nip_input = st.text_input("Podaj NIP (sam numer, bez kresek):", max_chars=10)

if st.button("🔍 Znajdź firmę i generuj dokument"):
    if not nip_input:
        st.warning("Proszę wpisać NIP.")
    else:
        try:
            gus = GUS(api_key=api_key)
            dane_raw = gus.search(nip=nip_input)
            
            # DIAGNOSTYKA - Pokaż co widzi GUS (dla Ciebie, żebyś wiedział co się dzieje)
            with st.expander("Kliknij tutaj, aby zobaczyć surowe dane z GUS (do sprawdzenia błędów)"):
                st.write("To są dane, które otrzymujemy z urzędu:")
                st.json(dane_raw)

            # Inteligentne wyciąganie danych
            info = wyciagnij_dane_smart(dane_raw)
            
            if not info['miasto']:
                st.error("GUS zwrócił dane firmy, ale brakuje w nich adresu. Sprawdź sekcję 'surowe dane' powyżej.")
            
            st.success(f"Znaleziono: **{info['nazwa']}**")
            
            # Generowanie pliku
            plik_word = generuj_word(info, nip_input)
            
            st.markdown("### 👇 Pobierz gotowy plik:")
            st.download_button(
                label="📥 POBIERZ PEŁNOMOCNICTWO (DOCX)",
                data=plik_word,
                file_name=f"Pelnomocnictwo_BDO_{nip_input}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        except Exception as e:
            st.error(f"Wystąpił błąd. (Szczegóły: {e})")
