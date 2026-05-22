import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import re
from config import (load_data, DESIGN_GROUPS, ALL_DESIGNS,
                    GROUP_COLORS, DESIGN_COL, short_label,
                    REALISTIC_EXTRAP_POINTS)

# ============================================
# Page config
# ============================================
st.set_page_config(
    page_title="DFT/FFT Synthesis Dashboard",
    page_icon="📊",
    layout="wide",
)

# ============================================
# Load data
# ============================================
df_filtered = load_data()

st.title("📊 DFT/FFT Synthesis Dashboard")
st.caption(f"Comparing {len(df_filtered)} FFT configurations across "
           f"{len(DESIGN_GROUPS)} architectures")

# ============================================
# Sidebar — global filters
# ============================================
st.sidebar.header("🎛️ Filters")

selected_archs = st.sidebar.multiselect(
    "Select Architecture(s):",
    options=list(DESIGN_GROUPS.keys()),
    default=list(DESIGN_GROUPS.keys()),
)

chart_style = st.sidebar.radio(
    "Chart Style:",
    options=['Line + Markers', 'Bar Chart'],
    index=0,
)
style = 'line' if chart_style == 'Line + Markers' else 'bar'

# ============================================
# 📊 Filtered Data Table
# ============================================
st.subheader("📊 Filtered Data")

col1, col2 = st.columns(2)
with col1:
    table_archs = st.multiselect(
        "Filter by Architecture:",
        options=list(DESIGN_GROUPS.keys()),
        default=list(DESIGN_GROUPS.keys()),
        key='table_arch'
    )
with col2:
    table_designs = st.multiselect(
        "Filter by Design (leave empty for all):",
        options=ALL_DESIGNS,
        format_func=short_label,
        key='table_design'
    )

dff = df_filtered.copy()
if table_archs:
    dff = dff[dff['Architecture'].isin(table_archs)]
else:
    dff = dff.iloc[0:0]
if table_designs:
    dff = dff[dff[DESIGN_COL].isin(table_designs)]

st.dataframe(dff.drop(columns=['short_name']), use_container_width=True)

# ============================================
# Helper: build chart
# ============================================
def build_chart(metric, style, selected_archs, title):
    fig = go.Figure()
    for arch in selected_archs:
        sub = df_filtered[df_filtered['Architecture'] == arch]
        if sub.empty:
            continue
        color = GROUP_COLORS.get(arch, '#95a5a6')
        if style == 'bar':
            fig.add_trace(go.Bar(
                x=sub['short_name'], y=sub[metric],
                name=arch,
                marker=dict(color=color, line=dict(color='white', width=1)),
                text=sub[metric].round(2), textposition='outside'
            ))
        else:
            fig.add_trace(go.Scatter(
                x=sub['short_name'], y=sub[metric],
                mode='lines+markers+text', name=arch,
                line=dict(color=color, width=3),
                marker=dict(size=12, line=dict(width=2, color='white')),
                text=sub[metric].round(2), textposition='top center'
            ))
    fig.update_layout(
        title=f'<b>{title}</b>',
        xaxis_title='Configuration', yaxis_title=metric,
        template='plotly_white', hovermode='x unified', height=600,
        legend=dict(orientation='h', yanchor='bottom', y=1.02,
                    xanchor='right', x=1),
        barmode='group',
    )
    return fig

# ============================================
# Cell count chart
# ============================================
st.plotly_chart(
    build_chart('cell count', style, selected_archs,
                'Cell Count Across FFT Configurations'),
    use_container_width=True
)

# ============================================
# 📈 Additional Metrics
# ============================================
st.subheader("📈 Additional Metrics")

extra_metric = st.selectbox(
    "Select metric to compare:",
    options=['cell area(um^2)', 'netarea', 'total area(um^2)',
             'critical slack (ns)', 'frequency', 'Period'],
    index=2,
)
st.plotly_chart(
    build_chart(extra_metric, style, selected_archs,
                f'{extra_metric} Across FFT Configurations'),
    use_container_width=True
)

# ============================================
# 🔮 Extrapolation / Trend Fit
# ============================================
st.subheader("🔮 Extrapolation / Trend Fit")

col1, col2, col3 = st.columns(3)
with col1:
    extrap_metric = st.selectbox(
        "Metric to extrapolate:",
        options=['cell count', 'cell area(um^2)', 'netarea',
                 'total area(um^2)', 'critical slack (ns)'],
        index=3,
    )
with col2:
    fit_type = st.selectbox(
        "Fit Type:",
        options=['linear', 'poly2', 'poly3', 'log', 'power'],
        index=0,
    )
with col3:
    n_extrap = st.slider("Extrapolate # points ahead:",
                         min_value=0, max_value=4, value=4)


def fit_and_extrapolate(x, y, fit_type, n_extrap):
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    max_x = x.max()
    future_candidates = [v for v in REALISTIC_EXTRAP_POINTS if v > max_x]
    x_future = np.array(future_candidates[:n_extrap], dtype=float)
    x_all = np.concatenate([x, x_future])

    if fit_type == 'linear':
        coeffs = np.polyfit(x, y, 1)
        y_fit = np.polyval(coeffs, x_all)
        eq = f"y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}"
    elif fit_type == 'log':
        coeffs = np.polyfit(np.log(x), y, 1)
        y_fit = coeffs[0] * np.log(x_all) + coeffs[1]
        eq = f"y = {coeffs[0]:.3f}·ln(x) + {coeffs[1]:.3f}"
    elif fit_type == 'power':
        coeffs = np.polyfit(np.log(x), np.log(y), 1)
        y_fit = np.exp(coeffs[1]) * x_all ** coeffs[0]
        eq = f"y = {np.exp(coeffs[1]):.3f}·x^{coeffs[0]:.3f}"
    elif fit_type == 'poly2':
        coeffs = np.polyfit(x, y, 2)
        y_fit = np.polyval(coeffs, x_all)
        eq = f"y = {coeffs[0]:.3f}x² + {coeffs[1]:.3f}x + {coeffs[2]:.3f}"
    elif fit_type == 'poly3':
        coeffs = np.polyfit(x, y, 3)
        y_fit = np.polyval(coeffs, x_all)
        eq = (f"y = {coeffs[0]:.3f}x³ + {coeffs[1]:.3f}x² + "
              f"{coeffs[2]:.3f}x + {coeffs[3]:.3f}")

    y_in = y_fit[:len(x)]
    ss_res = np.sum((y - y_in) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return x_all, y_fit, x_future, eq, r2


def extract_x_value(name):
    m = re.search(r'sw(\d+)', name)
    if m:
        return float(m.group(1))
    m = re.search(r'B(\d+)_SW(\d+)', name)
    if m:
        return float(m.group(1)) * 10 + float(m.group(2))
    return None


fig = go.Figure()
eq_lines = []

for arch in selected_archs:
    sub = df_filtered[df_filtered['Architecture'] == arch].copy()
    if sub.empty:
        continue
    sub['x_num'] = sub['short_name'].apply(extract_x_value)
    sub = sub.dropna(subset=['x_num']).sort_values('x_num')
    if len(sub) < 2:
        continue

    color = GROUP_COLORS.get(arch, '#95a5a6')
    x = sub['x_num'].values
    y = sub[extrap_metric].values

    x_all, y_fit, x_future, eq, r2 = fit_and_extrapolate(
        x, y, fit_type, n_extrap)

    if 'sw' in sub['short_name'].iloc[0]:
        future_labels = [f'sw{int(xv)}' for xv in x_future]
    else:
        future_labels = [f'x={xv:.1f}' for xv in x_future]
    all_labels = list(sub['short_name']) + future_labels

    fig.add_trace(go.Scatter(
        x=all_labels, y=y_fit, mode='lines',
        name=f'{arch} (fit)',
        line=dict(color=color, width=2, dash='dot'),
    ))
    fig.add_trace(go.Scatter(
        x=list(sub['short_name']), y=y, mode='markers',
        name=f'{arch} (data)',
        marker=dict(size=14, color=color,
                    line=dict(width=2, color='white')),
    ))
    if n_extrap > 0 and len(x_future) > 0:
        fig.add_trace(go.Scatter(
            x=future_labels, y=y_fit[len(x):],
            mode='markers+text', name=f'{arch} (extrap)',
            marker=dict(size=14, color=color, symbol='star',
                        line=dict(width=2, color='black')),
            text=[f'{v:.1f}' for v in y_fit[len(x):]],
            textposition='top center',
        ))
    eq_lines.append((arch, color, eq, r2))

    # 👇 ADD THIS BELOW (outside the for loop, no indentation)
fig.update_layout(
    title='<b>Extrapolation / Trend Fit</b>',
    xaxis_title='Configuration',
    yaxis_title=extrap_metric,
    template='plotly_white',
    hovermode='x unified',
    height=600,
    legend=dict(orientation='h', yanchor='bottom', y=1.02,
                xanchor='right', x=1),
)

st.plotly_chart(fig, use_container_width=True)

# Optional: show fit equations
if eq_lines:
    st.markdown("### 📐 Fit Equations")
    for arch, color, eq, r2 in eq_lines:
        st.markdown(
            f"<span style='color:{color}'>●</span> **{arch}**: "
            f"`{eq}` &nbsp;&nbsp; R² = `{r2:.4f}`",
            unsafe_allow_html=True
        )

