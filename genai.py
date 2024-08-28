import streamlit as st
from neo4j import GraphDatabase
import openai

# Ustawienia połączenia z Neo4j
URI = "URI"
USER = "USER"
PASSWORD = "PASSWORD"

# Ustawienie klucza API OpenAI
openai.api_key = "klucz_open_ai"

# Funkcja do tworzenia połączenia z Neo4j
def create_connection(uri, user, password):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    return driver

# Funkcja do wykonywania zapytań Cypher
def run_query(driver, query, parameters=None):
    with driver.session() as session:
        result = session.run(query, parameters)
        return result.data()

# Inicjalizacja połączenia z Neo4j
driver = create_connection(URI, USER, PASSWORD)

# Funkcja do przekształcania zapytań w języku naturalnym na zapytania Cypher
def natural_language_to_cypher(query_text):
    messages = [
        {"role": "system", "content": """
            Jesteś asystentem, który odpowiada na pytania użytkownika w języku polskim. Twoim zadaniem jest przekształcenie pytań zadanych przez użytkownika w 
            języku naturalnym na zapytania Cypher, które następnie wykonujesz w bazie Neo4j. Wyniki z bazy danych przekształcasz w odpowiedź, 
            która jest zrozumiała i naturalna w języku polskim.

            Sekcja wyników zapytania zawiera wyniki zapytania Cypher wygenerowane na podstawie pytania użytkownika. 
            Informacje pochodzące z bazy danych są zawsze wiarygodne i nie należy ich kwestionować ani modyfikować na podstawie wewnętrznej wiedzy.

            Dodatkowo, oto nazwy węzłów i krawędzi dostępnych w bazie, z których będziesz korzystać:
            - Węzły: Zapach, Branza, Charakter, Efekt, RodzajWnetrza, Kolor, RodzinaZapachowa
            - Relacje: ZAWIERA, POSIADA_CHARAKTER, WYWOŁUJE_EFEKT, PASUJE_DO, MA_KOLOR, NALEŻY_DO_RODZINY

            Przykłady struktury relacji:
            - (z)-[:NALEŻY_DO_RODZINY]->(r)
            - (z)-[:PASUJE_DO]->(w)
            - (z)-[:MA_KOLOR]->(k)
            - (z)-[:WYWOŁUJE_EFEKT]->(e)

            Przykłady zapytań:
            1. Zapachy wraz z ich rodzinami zapachowymi:
                MATCH (z:Zapach)-[:NALEŻY_DO_RODZINY]->(r:RodzinaZapachowa) RETURN z.nazwa_zapachu, r.nazwa LIMIT 10;

            2. Zapachy wraz z ich kolorami:
                MATCH (z:Zapach)-[:MA_KOLOR]->(k:Kolor) RETURN z.nazwa_zapachu, k.nazwa LIMIT 10;

            3. Zapachy wraz z rodzajami wnętrza:
                MATCH (z:Zapach)-[:PASUJE_DO]->(r:RodzajWnetrza) RETURN z.nazwa_zapachu, r.nazwa LIMIT 10;

            Przykład:
            - Pytanie użytkownika: Jakie zapachy są odpowiednie dla hoteli i mają kolor czerwony?

            Zapytanie Cypher: 
                MATCH (z:Zapach)-[:PASUJE_DO]->(w:RodzajWnetrza) 
                MATCH (z)-[:MA_KOLOR]->(k:Kolor) 
                RETURN z.nazwa_zapachu;

            - Odpowiedź naturalna: Zapachy odpowiednie dla hoteli i mające kolor czerwony to te, które są ciepłe i przyjazne.

            W swoich odpowiedziach używaj tylko dostępnych typów relacji i właściwości. Nie używaj żadnych innych typów relacji ani właściwości, które nie są dostępne.

            Bardzo ważne jest abyś odpowiadał zgodnie z prawdą, NIE WYMYŚLAŁ, jeśli nie znasz odpowiedzi to napisz po prostu "Niestety, nie znam odpowiedzi"
            
            """},
        {"role": "user", "content": f"Odpowiedz w języku naturalnym po otrzymaniu zapytania Cypher: {query_text}"}
    ]   
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        temperature=0.5,
    )
    full_response = response['choices'][0]['message']['content'].strip()

   

    # Rozdziel odpowiedź na język naturalny i zapytanie Cypher
    if "Zapytanie Cypher:" in full_response:
        natural_language_response, cypher_query = full_response.split("Zapytanie Cypher:", 1)
        natural_language_response = natural_language_response.strip()
        cypher_query = cypher_query.strip()
        # Wyciągnij rzeczywiste zapytanie Cypher z kodu
        lines = cypher_query.split("\n")
        cypher_query = ""
        for line in lines:
            if line.strip().startswith("MATCH") or line.strip().startswith("RETURN") or line.strip().startswith("WHERE"):
                cypher_query += line.strip() + " "
    else:
        natural_language_response = full_response
        cypher_query = None

    return natural_language_response, cypher_query

# Strona główna aplikacji Streamlit
st.title("Zapachowy chatbot")
st.write("Zadaj pytanie dotyczące zapachów w naturalnym języku:")

# Pole do wprowadzania zapytania przez użytkownika
user_input = st.text_input("Twoje pytanie:")

# Przycisk wyszukiwania
if st.button("Szukaj"):
    if user_input:
        # Konwersja zapytania na odpowiedź naturalną i Cypher
        natural_language_response, cypher_query = natural_language_to_cypher(user_input)
        st.write(f"Odpowiedź: {natural_language_response}")
        
        if cypher_query:
            st.write(f"Generowanie zapytania Cypher: {cypher_query}")
            # Wykonanie zapytania Cypher
            try:
                results = run_query(driver, cypher_query)
                if results:
                    st.write("Wyniki wyszukiwania:")
                    for result in results:
                        st.write(result)
                else:
                    st.write("Brak wyników spełniających zapytanie.")
            except Exception as e:
                st.write("Wystąpił błąd podczas przetwarzania zapytania:", str(e))


driver.close()