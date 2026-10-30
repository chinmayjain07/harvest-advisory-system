"""
Manual CSV/Excel upload processor for Agmarknet and MSAMB price sheets.
Handles diverse column headers, mixed date formats, APMC cleanup, and deduplication.
"""

import io
import re
import logging
from pathlib import Path
from typing import Dict, Any, Union

import pandas as pd

try:
    from database import get_connection
except ImportError:
    from src.database import get_connection

logger = logging.getLogger(__name__)

HEADER_SYNONYMS = {
    'arrival_date': ['arrival_date', 'arrival date', 'arrivaldate', 'date', 'arrival_dt', 'dt', 'arrival'],
    'commodity': ['commodity', 'crop', 'commodity_name', 'item', 'produce', 'crop_name'],
    'state': ['state', 'state_name'],
    'district': ['district', 'district_name'],
    'market': ['market', 'mandi', 'market_name', 'apmc', 'center', 'market_center', 'market center'],
    'variety': ['variety', 'commodity_variety', 'type'],
    'grade': ['grade', 'quality'],
    'min_price': ['min_price', 'min price', 'min', 'min_price(rs./quintal)', 'minimum_price', 'minimum price', 'min_price_rs_quintal'],
    'max_price': ['max_price', 'max price', 'max', 'max_price(rs./quintal)', 'maximum_price', 'maximum price', 'max_price_rs_quintal'],
    'modal_price': ['modal_price', 'modal price', 'modal', 'modal_price(rs./quintal)', 'modalprice', 'modal_price_rs_quintal']
}


class MandiUploadService:
    def __init__(self):
        pass

    def _normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map heterogeneous headers to standardized schema names."""
        col_map = {}
        for col in df.columns:
            raw = str(col).strip().lower()
            clean_space = re.sub(r'[^a-z0-9]+', ' ', raw).strip()
            clean_under = re.sub(r'[^a-z0-9]+', '_', raw).strip()
            
            matched_target = None
            # Exact match in synonyms
            for target_col, synonyms in HEADER_SYNONYMS.items():
                if raw in synonyms or clean_space in synonyms or clean_under in synonyms:
                    matched_target = target_col
                    break
            
            # Fuzzy / token match if not directly matched
            if not matched_target:
                tokens = clean_space.split()
                if any(t in tokens for t in ['market', 'mandi', 'apmc', 'center']):
                    matched_target = 'market'
                elif any(t in tokens for t in ['commodity', 'crop']):
                    matched_target = 'commodity'
                elif 'date' in tokens or 'arrival' in tokens:
                    matched_target = 'arrival_date'
                elif 'modal' in tokens:
                    matched_target = 'modal_price'
                elif 'min' in tokens or 'minimum' in tokens:
                    matched_target = 'min_price'
                elif 'max' in tokens or 'maximum' in tokens:
                    matched_target = 'max_price'

            col_map[col] = matched_target if matched_target else clean_under

        df = df.rename(columns=col_map)
        return df

    def _clean_and_validate_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize date, text columns, clean APMC suffix, and scale per-kg typos."""
        df = df.copy()

        # Check required columns
        required = ['arrival_date', 'commodity', 'market', 'modal_price']
        for req in required:
            if req not in df.columns:
                raise ValueError(f"Uploaded file missing essential column: '{req}'")

        # Parse dates to YYYY-MM-DD
        df['arrival_date'] = pd.to_datetime(df['arrival_date'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
        df = df.dropna(subset=['arrival_date'])

        # Text cleaning
        df['commodity'] = df['commodity'].astype(str).str.strip().str.title()
        df['state'] = df['state'].fillna('Maharashtra').astype(str).str.strip().str.title() if 'state' in df.columns else 'Maharashtra'
        df['district'] = df['district'].fillna('Pune').astype(str).str.strip().str.title() if 'district' in df.columns else 'Pune'
        
        # Clean APMC suffix
        df['market'] = df['market'].astype(str).apply(lambda m: re.sub(r'\s+APMC\b', '', m, flags=re.IGNORECASE).strip().title())
        df['variety'] = df['variety'].fillna('Other').astype(str).str.strip().str.title() if 'variety' in df.columns else 'Other'
        df['grade'] = df['grade'].fillna('FAQ').astype(str).str.strip().str.upper() if 'grade' in df.columns else 'FAQ'

        # Price parsing
        df['modal_price'] = pd.to_numeric(df['modal_price'], errors='coerce')
        df = df.dropna(subset=['modal_price'])

        if 'min_price' in df.columns:
            df['min_price'] = pd.to_numeric(df['min_price'], errors='coerce').fillna(df['modal_price'] * 0.95)
        else:
            df['min_price'] = df['modal_price'] * 0.95

        if 'max_price' in df.columns:
            df['max_price'] = pd.to_numeric(df['max_price'], errors='coerce').fillna(df['modal_price'] * 1.05)
        else:
            df['max_price'] = df['modal_price'] * 1.05

        # Handle per-kg typos: prices between 1 and 50 are usually Rs/kg, scale to Rs/quintal
        mask_per_kg = (df['modal_price'] > 0) & (df['modal_price'] < 50)
        df.loc[mask_per_kg, 'modal_price'] *= 100
        df.loc[mask_per_kg, 'min_price'] *= 100
        df.loc[mask_per_kg, 'max_price'] *= 100

        # Filter out extreme anomalies
        df = df[df['modal_price'] >= 50]

        return df

    def process_uploaded_file(self, file_path_or_buffer: Union[str, Path, io.BytesIO, io.StringIO]) -> Dict[str, Any]:
        """
        Process CSV or Excel file, clean records, deduplicate, and insert into SQLite.
        """
        try:
            # Read file based on extension or buffer type
            if isinstance(file_path_or_buffer, (str, Path)):
                path = Path(file_path_or_buffer)
                if not path.exists():
                    return {
                        "success": False,
                        "rows_processed": 0,
                        "rows_inserted": 0,
                        "duplicates_skipped": 0,
                        "commodity_summary": {},
                        "message": f"File not found: {path}"
                    }
                if path.suffix.lower() in ['.xlsx', '.xls']:
                    df_raw = pd.read_excel(path)
                else:
                    df_raw = pd.read_csv(path)
            else:
                # Buffer input
                try:
                    df_raw = pd.read_csv(file_path_or_buffer)
                except Exception:
                    file_path_or_buffer.seek(0)
                    df_raw = pd.read_excel(file_path_or_buffer)

        except Exception as e:
            return {
                "success": False,
                "rows_processed": 0,
                "rows_inserted": 0,
                "duplicates_skipped": 0,
                "commodity_summary": {},
                "message": f"Failed to read file: {str(e)}"
            }

        total_rows = len(df_raw)
        if total_rows == 0:
            return {
                "success": True,
                "rows_processed": 0,
                "rows_inserted": 0,
                "duplicates_skipped": 0,
                "commodity_summary": {},
                "message": "Uploaded file is empty."
            }

        try:
            df_norm = self._normalize_column_names(df_raw)
            df_clean = self._clean_and_validate_records(df_norm)
        except Exception as e:
            return {
                "success": False,
                "rows_processed": total_rows,
                "rows_inserted": 0,
                "duplicates_skipped": 0,
                "commodity_summary": {},
                "message": f"Validation error: {str(e)}"
            }

        conn = get_connection()
        cursor = conn.cursor()

        # Check existing combinations for deduplication
        inserted_count = 0
        skipped_count = 0
        commodity_summary = {}

        # Internal deduplication within the uploaded batch
        df_clean = df_clean.drop_duplicates(subset=['arrival_date', 'commodity', 'market', 'variety'])

        for _, row in df_clean.iterrows():
            comm = row['commodity']
            # Check duplicate in database
            check_q = """
            SELECT 1 FROM prices
            WHERE arrival_date = ? AND LOWER(commodity) = LOWER(?) AND LOWER(market) = LOWER(?) AND LOWER(variety) = LOWER(?)
            LIMIT 1
            """
            exists = cursor.execute(check_q, (row['arrival_date'], comm, row['market'], row['variety'])).fetchone()

            if exists:
                skipped_count += 1
            else:
                insert_q = """
                INSERT INTO prices (
                    arrival_date, commodity, state, district, market, variety, grade,
                    min_price, max_price, modal_price, is_interpolated, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'manual_upload')
                """
                cursor.execute(insert_q, (
                    row['arrival_date'], comm, row['state'], row['district'],
                    row['market'], row['variety'], row['grade'],
                    float(row['min_price']), float(row['max_price']), float(row['modal_price'])
                ))
                inserted_count += 1
                commodity_summary[comm] = commodity_summary.get(comm, 0) + 1

        conn.commit()
        conn.close()

        # Deduplicate count from batch filtering
        batch_duplicates = total_rows - (inserted_count + skipped_count)
        total_skipped = skipped_count + max(0, batch_duplicates)

        # Trigger incremental forecast refresh if new records inserted
        if inserted_count > 0:
            try:
                try:
                    from retrain_service import ForecastRefresher
                except ImportError:
                    from src.retrain_service import ForecastRefresher
                refresher = ForecastRefresher()
                refresher.refresh_all_forecasts()
            except Exception as e:
                logger.warning(f"Could not refresh forecasts after upload: {e}")

        return {
            "success": True,
            "rows_processed": total_rows,
            "rows_inserted": inserted_count,
            "duplicates_skipped": total_skipped,
            "commodity_summary": commodity_summary,
            "message": f"Successfully processed {total_rows} rows: {inserted_count} inserted, {total_skipped} skipped (duplicates/invalid)."
        }
