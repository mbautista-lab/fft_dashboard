import pandas as pd

# ============================================
# 📁 INPUT YOUR CSV FILE HERE
# ============================================
#CSV_FILE = '/Users/meriamb/SRAMS_calculator/FFT_dashboard_streamlit/synthesis_results.csv'
import os
CSV_FILE = os.path.join(os.path.dirname(__file__), 'synthesis_summary.csv')
CSV_FILE_DFT = os.path.join(os.path.dirname(__file__), 'dft_components.csv') 
# ============================================

# Design groups - 4 architecture families
DESIGN_GROUPS = {
    'Flexible MixedFFT (NOROM)': [
        'Flexible_MixedFFT_N64_K6_P11_B1_SW2_NOROM',
        'Flexible_MixedFFT_N64_K6_P11_B1_SW4_NOROM',
        'Flexible_MixedFFT_N64_K6_P11_B2_SW2_NOROM',
        'Flexible_MixedFFT_N64_K6_P11_B2_SW4_NOROM',
    ],
    'Flexible MixedFFT (with ROM)': [
        'Flexible_MixedFFT_N64_K6_P11_B1_SW2',
        'Flexible_MixedFFT_N64_K6_P11_B1_SW4',
        'Flexible_MixedFFT_N64_K6_P11_B2_SW2',
        'Flexible_MixedFFT_N64_K6_P11_B2_SW4',
    ],
    'Iterative MixedFFT96': [
        'Iterative_MixedFFT96_sw2',
        'Iterative_MixedFFT96_sw4',
        'Iterative_MixedFFT96_sw8',
        'Iterative_MixedFFT96_sw16',
    ],
    'Streaming FFT96': [
        'Streaming_FFT96_sw2',
        'Streaming_FFT96_sw4',
        'Streaming_FFT96_sw8',
        'Streaming_FFT96_sw16',
    ],

    # ===== NEW DFT/component architectures =====
    'ArrayMAC': [
        'GEMM_1x2_32',
        'GEMM_1x4_32', 
        'GEMM_1x8_32',
        'GEMM_1x16_32',
    ],

    'Butterfly': [
        'Bfly_2', 
        'Bfly_4', 
        'Bfly_8', 
        'Bfly_16',
    ],
    'Pad': [
        'PadUnit_sw2_64', 
        'PadUnit_sw4_64', 
        'PadUnit_sw8_64', 
        'PadUnit_s16_64',
    ],
    'Permute': [
        'PermuteUnit_sw2_64', 
        'PermuteUnit_sw4_64',
        'PermuteUnit_sw8_64', 
        'PermuteUnit_sw16_64',
    ],
    'Scatter-Gather': [
        'AddressingUnit_sw2_64', 
        'AddressingUnit_sw4_64',
        'AddressingUnit_sw8_64', 
        'AddressingUnit_sw16_64',
    ],
    'TRSM(128x128)': [
        'TRSM_sw2_32', 
        'TRSM_sw4_32', 
        'TRSM_sw8_32', 
        'TRSM_sw16_32',
    ],
    'TRSM(128x16)': [
        'TRSM_128x16_sw2_32', 
        'TRSM_128x16_sw4_32',
        'TRSM_128x16_sw8_32', 
        'TRSM_128x16_sw16_32',
    ],
}

ALL_DESIGNS = [d for group in DESIGN_GROUPS.values() for d in group]
DESIGN_COL = 'circuits'

# Color schemes
GROUP_COLORS = {
    'Flexible MixedFFT (NOROM)': '#3498db',
    'Flexible MixedFFT (with ROM)': '#9b59b6',
    'Iterative MixedFFT96': '#e74c3c',
    'Streaming FFT96': '#2ecc71',

     # New_dft_components
    'ArrayMAC': '#f39c12',
    'Butterfly': '#1abc9c',
    'Pad': '#e67e22',
    'Permute': '#34495e',
    'Scatter-Gather': '#16a085',
    'TRSM(128x128)': '#c0392b',
    'TRSM(128x16)': '#d35400',
}

GROUP_BG_COLORS = {
    'Flexible MixedFFT (NOROM)': '#ebf5fb',
    'Flexible MixedFFT (with ROM)': '#f4ecf7',
    'Iterative MixedFFT96': '#fdedec',
    'Streaming FFT96': '#eafaf1',
    'ArrayMAC': '#fef5e7',
    'Butterfly': '#e8f8f5',
    'Pad': '#fdf2e9',
    'Permute': '#ebeef1',
    'Scatter-Gather': '#e8f6f3',
    'TRSM(128x128)': '#fadbd8',
    'TRSM(128x16)': '#fae5d3',
}

# Realistic extrapolation points
REALISTIC_EXTRAP_POINTS = [32, 64, 96, 128, 256]


def get_group(name):
    """Return architecture group for a given design name."""
    for group, designs in DESIGN_GROUPS.items():
        if name in designs:
            return group
    return 'Other'


def short_label(name):
    """Make a short, readable label from a long design name."""
    if name.endswith('_NOROM'):
        return name.replace('Flexible_MixedFFT_N64_K6_P11_', '').replace('_NOROM', '')
    if name.startswith('Flexible_MixedFFT_N64_K6_P11_'):
        return name.replace('Flexible_MixedFFT_N64_K6_P11_', '')
    if name.startswith('Iterative_MixedFFT96_'):
        return name.replace('Iterative_MixedFFT96_', '')
    if name.startswith('Streaming_FFT96_'):
        return name.replace('Streaming_FFT96_', '')
    return name
      # New shorteners
    if name.startswith('GEMM_'):
        return name.replace('GEMM_', '').replace('_32', '')
    if name.startswith('Bfly_'):
        return name  # already short
    if name.startswith('PadUnit_'):
        return name.replace('PadUnit_', '').replace('_64', '')
    if name.startswith('PermuteUnit_'):
        return name.replace('PermuteUnit_', '').replace('_64', '')
    if name.startswith('AddressingUnit_'):
        return name.replace('AddressingUnit_', '').replace('_64', '')
    if name.startswith('TRSM_128x16_'):
        return name.replace('TRSM_128x16_', '').replace('_32', '')
    if name.startswith('TRSM_'):
        return name.replace('TRSM_', '').replace('_32', '')
    return name


def _normalize_columns(df):
    """Make column names consistent across CSV files."""
    df.columns = (
        df.columns.str.strip()
                  .str.replace('²', '2', regex=False)
                  .str.replace('_', ' ', regex=False)   # cell_area → cell area
    )
    return df


def load_data():
    """Load both CSVs, merge, filter to known designs, and add helper columns."""
    # --- Load original FFT data ---
    df1 = pd.read_csv(CSV_FILE)
    df1 = _normalize_columns(df1)

    # --- Load new DFT/component data ---
    df2 = pd.read_csv(CSV_FILE_DFT)
    df2 = _normalize_columns(df2)

    # Drop the leftmost label column if it exists (it's the sparse arch name)
    # The first unnamed column in your new CSV holds 'ArrayMAC', 'Butterfly', etc.
    first_col = df2.columns[0]
    if first_col.lower().startswith('unnamed') or first_col == '':
        df2 = df2.drop(columns=[first_col])

    # Strip whitespace from the circuits column (your new CSV has trailing spaces!)
    if DESIGN_COL in df2.columns:
        df2[DESIGN_COL] = df2[DESIGN_COL].astype(str).str.strip()

    # Drop empty separator rows
    df2 = df2.dropna(subset=[DESIGN_COL])
    df2 = df2[df2[DESIGN_COL] != 'nan']

    # --- Combine ---
    df = pd.concat([df1, df2], ignore_index=True, sort=False)

    # Filter and tag
    df_filtered = df[df[DESIGN_COL].isin(ALL_DESIGNS)].reset_index(drop=True)
    df_filtered['Architecture'] = df_filtered[DESIGN_COL].apply(get_group)
    df_filtered['short_name'] = df_filtered[DESIGN_COL].apply(short_label)
    return df_filtered