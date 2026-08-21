import pandas as pd
import numpy as np

# 1. Wczytanie surowych danych
print('====================================')
df = pd.read_csv('financial_transactions_raw.csv')
print('Profilowanie danych'.center(50, '-').upper())

# 2. Rozmiar zbioru
print('====================================')
print(f'Liczba rekordów: {df.shape[0]}, liczba kolumn: {df.shape[1]}')

# 3. Typy danych oraz braki
print('====================================')
print('Typy danych oraz braki')
print(df.info())

# 4. Podgląd rekordów
print('====================================')
print(df.head())

# 5. Analiza wartości null
print('====================================')
print('Liczba nulli w poszczególnych kolumnach')
print(df.isna().sum())

# 6. Analiza występywania duplikatów
print('====================================')
print(f'Liczba duplikujących się rekordów: {df.duplicated().sum()}')

print('====================================')
print('Standaryzacja struktury i usunięcie duplikatów'.center(50, '-').upper())

# 1. Usunięcie skrajnych spacji, zamiana spacji oraz myślników na podłogi, sprowadzenie do małych liter
print('Usunięcie skrajnych spacji, zamiana spacji i myślników na podłogi, modyfikacja to małych liter')
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(' ', '_')
    .str.replace('-', '_')
)
print('Ustandaryzowane nazwy kolumn'.center(50, '-').upper())
print(df.columns.to_list())

# 2. Usunięcie duplikujących się rekordów
print('====================================')
wiersze_poczatkowe = len(df)
df = df.drop_duplicates()
print(f'Usunięto {wiersze_poczatkowe - len(df)} duplikujących się rekordów')

# 3. Usunięcie rekordów bez ID transakcji (klucz główny), bez trans_id niemożliwe jest uzgodnienie sald
print('====================================')
liczba_brakujacych_id = df['trans_id'].isna().sum()
df = df.dropna(subset=['trans_id'])
print(f'Usunięte rekordy bez trans_id: {liczba_brakujacych_id}, pozostałe rekordy: {len(df)}')

print('====================================')
print('Czyszczenie tekstów i mapowanie krajów'.center(50, '-').upper())

# 1. Czyszczenie danych klienta (client_name)
print('====================================')
print('Czyszczenie danych klienta -> zamiana pierwszych liter na wielkie, strip spacji')
df['client_name'] = df['client_name'].str.strip().str.title().replace(['Nan',''], np.nan)

# 2. Standaryzacja tickerów
print('====================================')
print('Standaryzacja tickerów')
df['ticker_symbol'] = df['ticker_symbol'].str.strip().str.upper().replace(['NAN',''], np.nan)

# 3. Ujednolicenie klas aktywów
print('====================================')
print('Strip spacji i ujednolicenie wariantów')
df["asset_class"] = df["asset_class"].str.strip().str.title()
aktywa_zamiana = {
    "Fixed_Income": "Fixed Income",
    "Crypto": "Cryptocurrency",
    "Nan": np.nan,
}
df["asset_class"] = df["asset_class"].replace(aktywa_zamiana)

# 4. Standaryzacja kodów krajów na ISO
print('====================================')
print('Ujednolicenie kodów ISO dla krajów')
kraje_mapowanie = {
    "Poland": "PL",
    "POL": "PL",
    "USA": "US",
    "United Kingdom": "UK",
    "Germany": "DE",
    "Italy": "IT",
    "France": "FR",
    "Sweden": "SE",
}
df['country'] = df['country'].str.strip().replace(kraje_mapowanie).replace(['nan',''], np.nan)


print('====================================')
print('Czyszczenie i konwersja danych numerycznych'.center(50, '-').upper())

# 1. Czyszczenie i konwersja 'volume' (Wolumen transakcji)
print('====================================')
print('Usunięcie przecinków (1,000 -> 1000) oraz strip nadmiarowych spacji')
df["volume"] = df["volume"].astype(str).str.replace(",", "").str.strip()
print('Zamiana liczb w postaci string na numeric')
df["volume"] = pd.to_numeric(df["volume"])
print('Wolumen musi byc dodatni, więc zamiana w przypadku błędów przy pomocy abs()')
df["volume"] = df["volume"].abs()

# 2. Czyszczenie i konwersja 'price_per_share'
print('====================================')
print('Usunięcie wszystkiego oprócz cyfr, kropek i minusów (np. $150.50 -> 150.50 albo 120.50 EUR -> 120.50')
df['price_per_share'] = (
    df['price_per_share']
    .str.replace(r'[^\d.-]', '', regex=True)
    .str.strip()
)
# Konwersja na typ float ze string
df['price_per_share'] = pd.to_numeric(df['price_per_share'])

# Cena nie może być ujemna ani = 0, zamiana <= 0 na NaN żeby poźniej zweryfikować/usunąć
df.loc[df['price_per_share'] <= 0, 'price_per_share'] = np.nan


# 3. Czyszczenie i konwersja 'commission_fee'
print('====================================')
print('Prowizja jako koszt, nie może być ujemna -> zamiana wartości bezweględnej przez abs()')
df['commission_fee'] = df['commission_fee'].abs()
print('Brak wpisu o prowizji może oznaczać transakcje bezprowizyjną')
df['commission_fee'] = df['commission_fee'].fillna(0.0)

print('====================================')
print('Daty, kalkulacje finansowe i zapis pliku'.center(50, '-').upper())

# 1. Standaryzacja niespójnych formatów dat
print('====================================')
print('Wykorzystanie pd.to_datetime z formatem =mixed aby obsłużyć jednocześnie różne formatowania dat oraz errors=coerce w celu zamiany ciągów tekstowych typu invalid_date na NaT')
df['trade_date']=pd.to_datetime(
    df['trade_date'], format='mixed',errors='coerce')

print('Transakcje bez daty uznajemy za bezwartościowe audytowo, usuwamy je z uwzględnieniem copy()')
df = df.dropna(subset=['trade_date'].copy())

print('Standaryzacja formatu dat na YYYY-MM-DD')
df['trade_date'] = df['trade_date'].dt.strftime('%Y-%m-%d')

# 2. Stworzenie nowej kolumny total_value
print('====================================')
print('Dodanie kolumny total_value -> wartość transakcji brutto -> (wolumen * cena za akcję) + prowizja')
print('total_values')
df['total_value'] = (df['volume'] * df['price_per_share']) + df['commission_fee']
df['total_value'] = df['total_value'].round(2)
print(df['total_value'].to_string())

# 3. Czyszczenie pozostałych wartości brakujących
print('====================================')
print('Czyszczenie pozostałych NaN -> w kolumnach krytycznych t.j. client_name, price_per_share, ticker_symbol -> brak danych uniemożliwia dalszą analizę')
df = df.dropna(subset=['client_name', 'price_per_share', 'ticker_symbol']).copy()

# 4. Zmiana kolejności kolumn
print('====================================')
print('Zmiana kolejności kolumn')
kolejnosc_kolumn = [
    'trans_id',
    'trade_date',
    'client_name',
    'country',
    'asset_class',
    'ticker_symbol',
    'volume',
    'price_per_share',
    'commission_fee',
    'total_value'
]
print('Nowa kolejność kolumn')
df = df[kolejnosc_kolumn]

# 5. Podsumowanie końcowe czyszczenia i eksport do CSV
print('====================================')
print('Inspekcja całego zbioru po czyszczeniu')
print(df.info())
print('====================================')
print('Podgląd pierwszych 5 rekordów po czyszczeniu')
print(df.head().to_string())
print('====================================')
print(f'Suma wartości brakujących po czyszczeniu \n {df.isna().sum()}')
print('====================================')
df.to_csv("clean_financial_transactions.csv", index=False)
print('Plik clean_financial_transactions.csv został pomyślnie zapisany')


print('====================================')
print('Agregacja danych i proste podsumowanie danych per inwestor'.center(50, '-').upper())

# 1. Agregacja kluczowych wskaźników per inwestor
client_summary = (
    df.groupby('client_name')
    .agg(
        total_invested=('total_value', 'sum'),
        avg_trade_size=('total_value', 'mean'),
        trade_count=('trans_id', 'count')
    )
    .round(2)
    .reset_index()
    .sort_values(by='total_invested', ascending=False)
)

print('====================================')
print('Raport per inwestor')
print(client_summary.to_string(index=False))
print('====================================')
client_summary.to_csv("financial_transaction_per_investor.csv", index=False)
print('Plik financial_transaction_per_investor.csv został pomyślnie zapisany')