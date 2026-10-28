import pandas as pd

tomato = pd.read_csv('data/raw/Agri-Research Large Tomato Dataset.csv')
tomato['Clean_Date'] = pd.to_datetime(tomato['Arrival_Date'], dayfirst=True)
print("--- Tomato Jan 2025 ---")
print(tomato[(tomato['Clean_Date'] >= '2025-01-20') & (tomato['Clean_Date'] <= '2025-02-05')][['Clean_Date', 'Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])

onion = pd.read_csv('data/raw/Agri-Research Large Onion Dataset.csv')
onion['Clean_Date'] = pd.to_datetime(onion['Arrival_Date'], dayfirst=True)
print("\n--- Onion around Feb 2023 ---")
print(onion[(onion['Clean_Date'] >= '2023-02-15') & (onion['Clean_Date'] <= '2023-03-01')][['Clean_Date', 'Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
