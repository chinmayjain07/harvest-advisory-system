import pandas as pd

df = pd.read_csv('data/raw/Agri-Research Large Potato Dataset.csv')
df['Clean_Date'] = pd.to_datetime(df['Arrival_Date'], dayfirst=True)
pune = df[df['Market'].str.startswith('Pune')].sort_values('Clean_Date')

print("--- Potato around 2024-02-18 in Pune ---")
print(pune[(pune['Clean_Date'] >= '2024-02-10') & (pune['Clean_Date'] <= '2024-02-25')][['Clean_Date', 'Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])

print("\n--- Potato around 2025-07-14 in Pune ---")
print(pune[(pune['Clean_Date'] >= '2025-07-05') & (pune['Clean_Date'] <= '2025-07-25')][['Clean_Date', 'Market', 'Variety', 'Min_Price', 'Max_Price', 'Modal_Price']])
