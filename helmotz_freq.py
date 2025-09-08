import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Helmholtz Resonance Calculator", page_icon="https://images.squarespace-cdn.com/content/v1/658043d6c66e634cdbc7a4cc/8b08c99b-d2f0-4e8d-acfd-a91b08c6a4ed/Logo-Lydech-avec-baseline-h240.png?format=1500w", layout="centered", initial_sidebar_state="expanded")

# Cache expensive calculations for better responsiveness on Streamlit Cloud
@st.cache_data
def calculate_holes_from_spacing(D_mm, spacing_mm):
    """Calculate number of holes in square arrangement within a circle"""
    radius = D_mm / 2
    grid_points = int(D_mm // spacing_mm)
    start = -((grid_points - 1) * spacing_mm) / 2
    positions = [start + i * spacing_mm for i in range(grid_points)]
    return sum(1 for x in positions for y in positions if math.hypot(x, y) <= radius)

def calculate_metrics(inputs):
    """Calculate all acoustic parameters and frequency"""
    try:
        hole_mode = inputs.get('hole_mode', 'Standard')
        volume_mode = inputs.get('volume_mode', 'Standard')
        calc_mode = inputs.get('mode', 'Number')

        # Unit conversions
        c = 20.05 * math.sqrt(273.15 + inputs['temp'])
        D = inputs['D'] / 1000  # mm to m
        t = inputs['t'] / 1000  # mm to m

        # Material area (for OA% and standard volume)
        material_area = math.pi * (D / 2) ** 2 if D > 0 else 0.0  # m²

        # Volume
        if volume_mode == 'Standard':
            L = inputs['L'] / 1000  # mm to m
            V = material_area * L  # m³
        else:  # Direct Volume
            V = inputs['V'] / 1000  # L to m³

        # Opening area and effective length
        if hole_mode == 'Standard':
            d = inputs['d'] / 1000  # mm to m
            hole_area = math.pi * (d / 2) ** 2  # m²

            # Number of holes
            if calc_mode == 'Number':
                N = inputs['N']
            elif calc_mode == 'Density':
                N = int(inputs['density'] * (material_area * 10000))
            elif calc_mode == 'OA%':
                N = int(max(0.0, (inputs['OA'] / 100.0 * material_area)) / hole_area)
            elif calc_mode == 'Spacing':
                spacing_mm = inputs['spacing']
                spacing_cm = spacing_mm / 10.0
                density = 1.0 / (spacing_cm ** 2)
                N = int(density * (material_area * 10000))
                N = max(N, 1)
            else:
                N = inputs.get('N', 0)

            A = N * hole_area  # m²
            Leff = t + 1.7 * d / 2  # effective length with correction
        else:  # Direct Input (single neck)
            A = inputs['A']  # m²
            Leff = inputs['Leff'] / 1000  # mm to m
            N = 0
            d = 0.0

        if A <= 0 or V <= 0 or Leff <= 0:
            raise ValueError("Invalid parameters combination")

        f0 = inputs['k'] * (c / (2 * math.pi)) * math.sqrt(A / (V * Leff))

        # Derived metrics
        if hole_mode == 'Standard':
            if calc_mode == 'Spacing':
                spacing_mm = inputs['spacing']
                OA_percent = ((math.pi * (d * 1000.0) ** 2) / (4.0 * (spacing_mm ** 2))) * 100.0
            else:
                OA_percent = (A / material_area) * 100.0 if material_area > 0 else 0.0

            density = (N / (material_area * 10000.0)) if material_area > 0 else 0.0
            spacing = (math.sqrt(1.0 / (N / (material_area * 10000.0))) * 10.0 if N and material_area > 0 else 0.0)
        else:
            OA_percent = (A / material_area) * 100.0 if material_area > 0 else 0.0
            density = 0.0
            spacing = 0.0

        return {
            'f0': f0,
            'OA%': OA_percent,
            'density': density,
            'spacing': spacing,
            'N': N,
            'V': V * 1000.0,  # m³ to L
            'A': A,  # m²
            'Leff': Leff * 1000.0  # m to mm
        }

    except Exception as e:
        # Display a concise error to the user and return None
        st.error("Calculation error: " + str(e))
        return None

############################################
# Interface (English) with two calculation modes
############################################
st.title("Helmholtz Resonance Calculator")

mode_panel, mode_neck = st.tabs(["Perforated Panel", "Direct Neck"])  # separate user flows

# -----------------------------
# Perforated Panel mode
# -----------------------------
with mode_panel:
    with st.form("form_panel"):
        st.subheader("Panel and Holes")
        inputs_panel = {
            'temp': st.number_input("Temperature (°C)", -20.0, 250.0, 20.0, key="temp_panel"),
            'D': st.number_input("Panel diameter (mm)", 5.0, 2000.0, 100.0, key="D_panel"),
            't': st.number_input("Panel thickness (mm)", 0.05, 50.0, 1.0, key="t_panel"),
            'k': st.number_input("Correction factor k", 0.1, 2.0, 1.0, 0.1, key="k_panel"),
        }

        # Volume options for panel mode
        volume_mode_panel = st.radio("Cavity volume input:", ["Standard (Air gap)", "Direct (Volume)"] , horizontal=True, key="vol_mode_panel")
        inputs_panel['volume_mode'] = 'Standard' if volume_mode_panel.startswith("Standard") else 'Direct Input'
        if inputs_panel['volume_mode'] == 'Standard':
            inputs_panel['L'] = st.number_input("Air gap (mm)", 0.01, 500.0, 10.0, key="L_panel")
        else:
            inputs_panel['V'] = st.number_input("Volume (L)", 0.001, 500.0, 1.000, format="%.3f", help="Resonator cavity volume in liters.", key="V_panel")

        # Holes are always standard in this mode
        inputs_panel['hole_mode'] = 'Standard'
        inputs_panel['d'] = st.number_input("Hole diameter (mm)", 0.1, 200.0, 5.0, key="d_panel")
        calc_mode_panel = st.radio("Hole calculation mode:", ["Number", "Density", "OA%", "Spacing"], horizontal=True, key="calc_mode_panel")
        inputs_panel['mode'] = calc_mode_panel
        if calc_mode_panel == "Number":
            inputs_panel['N'] = st.number_input("Number of holes", 1, 200000, 100, key="N_panel")
        elif calc_mode_panel == "Density":
            inputs_panel['density'] = st.number_input("Holes/cm²", 0.001, 1000.0, 10.0, key="density_panel")
        elif calc_mode_panel == "OA%":
            inputs_panel['OA'] = st.number_input("Open Area (%)", 0.01, 80.0, 5.0, key="OA_panel")
        else:
            inputs_panel['spacing'] = st.number_input("Hole spacing (mm)", 0.1, 200.0, 10.0, key="spacing_panel")

        # Analysis controls (dynamic to mode)
        st.subheader("Parameter Analysis")
        vary_params_panel = ["None", "Temperature", "Panel thickness", "Panel diameter", "Correction factor"]
        if inputs_panel['volume_mode'] == 'Standard':
            vary_params_panel.append("Air gap")
        else:
            vary_params_panel.append("Volume")
        vary_params_panel.extend(["Hole diameter", "Number of holes", "Hole density", "OA%", "Hole spacing"])

        vary_param_panel = st.selectbox("Vary parameter:", vary_params_panel, key="vary_panel")
        param_range_panel = None
        if vary_param_panel != "None":
            col_min, col_max, col_steps = st.columns(3)
            with col_min:
                min_val_p = st.number_input("Min", value=1.0, key="min_panel")
            with col_max:
                max_val_p = st.number_input("Max", value=10.0, key="max_panel")
            with col_steps:
                steps_p = st.number_input("Steps", 10, 2000, 50, key="steps_panel")
            param_range_panel = np.linspace(min_val_p, max_val_p, int(steps_p))

        submit_panel = st.form_submit_button("Calculate (Panel)")

    # Compute on submit only; keep analysis in session_state
    if submit_panel:
        results = []
        base_inputs = inputs_panel.copy()

        if vary_param_panel == "None":
            metrics = calculate_metrics(base_inputs)
            if metrics:
                st.session_state['panel_last_metrics'] = metrics
                st.session_state['panel_last_inputs'] = base_inputs
                # Clear old analysis when switching from sweep to single calc
                st.session_state.pop('analysis_df_panel', None)
        else:
            progress = st.progress(0)
            for i, val in enumerate(param_range_panel):
                current = base_inputs.copy()
                # map varying parameter
                if vary_param_panel == "Temperature":
                    current['temp'] = val
                elif vary_param_panel == "Panel thickness":
                    current['t'] = val
                elif vary_param_panel == "Panel diameter":
                    current['D'] = val
                elif vary_param_panel == "Air gap":
                    current['L'] = val
                elif vary_param_panel == "Volume":
                    current['V'] = val
                elif vary_param_panel == "Hole diameter":
                    current['d'] = val
                elif vary_param_panel == "Hole density":
                    current['density'] = val
                    current['mode'] = "Density"
                elif vary_param_panel == "Number of holes":
                    current['N'] = int(val)
                    current['mode'] = "Number"
                elif vary_param_panel == "OA%":
                    current['OA'] = val
                    current['mode'] = "OA%"
                elif vary_param_panel == "Hole spacing":
                    current['spacing'] = val
                    current['mode'] = "Spacing"
                elif vary_param_panel == "Correction factor":
                    current['k'] = val

                metrics = calculate_metrics(current)
                if metrics:
                    results.append({'x': val, 'f0': metrics['f0'], **metrics})
                progress.progress((i + 1) / len(param_range_panel))

            if results:
                df = pd.DataFrame(results)
                st.session_state['analysis_df_panel'] = df
                st.session_state['vary_param_panel'] = vary_param_panel
                st.session_state['base_inputs_panel'] = base_inputs

    # Display area for results and analysis with internal tabs (Analysis first to avoid tab jump)
    tab_analysis_p, tab_calc_p = st.tabs(["Analysis", "Calculator"])

    with tab_calc_p:
        metrics = st.session_state.get('panel_last_metrics')
        base_inputs = st.session_state.get('panel_last_inputs')
        if metrics and base_inputs:
            cols = st.columns([2, 2, 3])
            cols[0].metric("Resonance Frequency", f"{metrics['f0']:.1f} Hz")
            cols[1].metric("Number of Holes", int(metrics['N']))
            if base_inputs['volume_mode'] == 'Standard':
                vol_text = f"Air gap: {base_inputs['L']:.2f} mm"
            else:
                vol_text = f"Volume: {metrics['V']:.3f} L"
            cols[2].info((f"{vol_text} | OA: {metrics['OA%']:.2f}% | Leff: {metrics['Leff']:.2f} mm"))
        else:
            st.info("Enter parameters and press Calculate (Panel).")

    with tab_analysis_p:
        if 'analysis_df_panel' in st.session_state:
            df = st.session_state['analysis_df_panel']
            vary_param = st.session_state['vary_param_panel']
            st.subheader(f"Resonance Frequency vs {vary_param}")
            st.line_chart(pd.DataFrame({'x': df['x'].values, 'f0': df['f0'].values}).set_index('x'))

            # Target selector before figure so we can overlay lines
            target_freq = st.number_input("Target frequency (Hz)", min_value=0.0, max_value=20000.0, value=1000.0, step=50.0, key="target_panel")
            min_f0 = df['f0'].min(); max_f0 = df['f0'].max()
            have_match = min_f0 <= target_freq <= max_f0
            x_val = None; f0_val = None
            if have_match:
                idx = np.abs(df['f0'] - target_freq).argmin()
                closest_row = df.iloc[idx]
                x_val = float(closest_row['x']); f0_val = float(closest_row['f0'])

            # Matplotlib plot with dashed crosshair lines
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df['x'], df['f0'], 'b-', lw=2)
            ax.set_xlabel(vary_param)
            ax.set_ylabel('Frequency (Hz)')
            ax.grid(True, alpha=0.4)
            # Horizontal dashed line at target frequency
            ax.axhline(y=target_freq, color='r', linestyle='--', alpha=0.6, label='Target f')
            # Vertical dashed line at matching parameter (if in range)
            if have_match and x_val is not None:
                ax.axvline(x=x_val, color='r', linestyle='--', alpha=0.6)
                ax.plot([x_val], [f0_val], 'ro', alpha=0.7)
            st.pyplot(fig)

            # Downloads of the figure and data
            png_buf = BytesIO(); pdf_buf = BytesIO()
            fig.savefig(png_buf, format='png', bbox_inches='tight', dpi=300)
            fig.savefig(pdf_buf, format='pdf', bbox_inches='tight')
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button("Download PNG", data=png_buf.getvalue(), file_name=f"helmholtz_panel_{vary_param}.png", mime="image/png")
            with c2:
                st.download_button("Download PDF", data=pdf_buf.getvalue(), file_name=f"helmholtz_panel_{vary_param}.pdf", mime="application/pdf")
            with c3:
                csv_buf = BytesIO(); df.to_csv(csv_buf, index=False)
                st.download_button("Download CSV", csv_buf.getvalue(), f"helmholtz_panel_{vary_param}.csv", "text/csv")

            # Text feedback
            if not have_match:
                st.warning("Target frequency is outside the plotted range.")
            else:
                st.success(f"Closest {vary_param}: {x_val:.3f} (f0 = {f0_val:.2f} Hz)")
        else:
            st.info("Run a parameter sweep from the form to see analysis.")

# -----------------------------
# Direct Neck mode
# -----------------------------
with mode_neck:
    with st.form("form_neck"):
        st.subheader("Direct Neck (single opening)")
        # Minimal inputs for direct single neck; we still pass D/t internally but they are not user-facing
        temp_neck = st.number_input("Temperature (°C)", -20.0, 250.0, 20.0, key="temp_neck")
        V_neck = st.number_input("Volume (L)", 0.001, 500.0, 1.000, format="%.3f", key="V_neck")
        d_neck = st.number_input("Neck diameter d (mm)", 0.1, 500.0, 30.0, key="d_neck")
        L_neck = st.number_input("Neck length L (mm) - effective", 0.01, 2000.0, 50.0, key="L_neck")
        k_neck = st.number_input("Correction factor k", 0.1, 2.0, 1.0, 0.1, key="k_neck")

        # Analysis controls for neck mode
        st.subheader("Parameter Analysis")
        vary_params_neck = ["None", "Temperature", "Volume", "Neck diameter", "Neck length", "Correction factor"]
        vary_param_neck = st.selectbox("Vary parameter:", vary_params_neck, key="vary_neck")
        param_range_neck = None
        if vary_param_neck != "None":
            cmin, cmax, csteps = st.columns(3)
            with cmin:
                min_val_n = st.number_input("Min", value=1.0, key="min_neck")
            with cmax:
                max_val_n = st.number_input("Max", value=10.0, key="max_neck")
            with csteps:
                steps_n = st.number_input("Steps", 10, 2000, 50, key="steps_neck")
            param_range_neck = np.linspace(min_val_n, max_val_n, int(steps_n))

        submit_neck = st.form_submit_button("Calculate (Neck)")

    if submit_neck:
        # Build inputs for calculate_metrics using direct-input route (A, Leff, V)
        A_neck = math.pi * ((d_neck / 1000.0) / 2) ** 2  # m²
        inputs_neck = {
            'temp': temp_neck,
            'D': 100.0,            # dummy for area (not used in direct mode display)
            't': 1.0,              # dummy thickness (mm)
            'k': k_neck,
            'volume_mode': 'Direct Input',
            'V': V_neck,
            'hole_mode': 'Direct Input',
            'A': A_neck,
            'Leff': L_neck,
        }

        if vary_param_neck == "None":
            metrics = calculate_metrics(inputs_neck)
            if metrics:
                st.session_state['neck_last_metrics'] = metrics
                st.session_state['neck_last_inputs'] = inputs_neck
                st.session_state['neck_dims'] = {'d': d_neck, 'L': L_neck}
                st.session_state.pop('analysis_df_neck', None)
        else:
            results = []
            progress = st.progress(0)
            for i, val in enumerate(param_range_neck):
                current = inputs_neck.copy()
                if vary_param_neck == "Temperature":
                    current['temp'] = val
                elif vary_param_neck == "Volume":
                    current['V'] = val
                elif vary_param_neck == "Neck diameter":
                    A_var = math.pi * ((val / 1000.0) / 2) ** 2
                    current['A'] = A_var
                elif vary_param_neck == "Neck length":
                    current['Leff'] = val
                elif vary_param_neck == "Correction factor":
                    current['k'] = val

                metrics = calculate_metrics(current)
                if metrics:
                    results.append({'x': val, 'f0': metrics['f0'], **metrics})
                progress.progress((i + 1) / len(param_range_neck))

            if results:
                df = pd.DataFrame(results)
                st.session_state['analysis_df_neck'] = df
                st.session_state['vary_param_neck'] = vary_param_neck
                st.session_state['base_inputs_neck'] = inputs_neck

    tab_analysis_n, tab_calc_n = st.tabs(["Analysis", "Calculator"])

    with tab_calc_n:
        metrics = st.session_state.get('neck_last_metrics')
        dims = st.session_state.get('neck_dims', {})
        if metrics:
            cols = st.columns([2, 3])
            cols[0].metric("Resonance Frequency", f"{metrics['f0']:.1f} Hz")
            cols[1].info((f"V: {metrics['V']:.3f} L | d: {dims.get('d', float('nan')):.2f} mm | L: {dims.get('L', float('nan')):.2f} mm | Leff: {metrics['Leff']:.2f} mm"))
        else:
            st.info("Enter parameters and press Calculate (Neck).")

    with tab_analysis_n:
        if 'analysis_df_neck' in st.session_state:
            df = st.session_state['analysis_df_neck']
            vary_param = st.session_state['vary_param_neck']
            st.subheader(f"Resonance Frequency vs {vary_param}")
            st.line_chart(pd.DataFrame({'x': df['x'].values, 'f0': df['f0'].values}).set_index('x'))

            # Target selector before figure so we can overlay lines
            target_freq = st.number_input("Target frequency (Hz)", min_value=0.0, max_value=20000.0, value=1000.0, step=50.0, key="target_neck")
            min_f0 = df['f0'].min(); max_f0 = df['f0'].max()
            have_match = min_f0 <= target_freq <= max_f0
            x_val = None; f0_val = None
            if have_match:
                idx = np.abs(df['f0'] - target_freq).argmin()
                closest_row = df.iloc[idx]
                x_val = float(closest_row['x']); f0_val = float(closest_row['f0'])

            # Matplotlib plot with dashed crosshair lines
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df['x'], df['f0'], 'b-', lw=2)
            ax.set_xlabel(vary_param)
            ax.set_ylabel('Frequency (Hz)')
            ax.grid(True, alpha=0.4)
            # Horizontal dashed line at target frequency
            ax.axhline(y=target_freq, color='r', linestyle='--', alpha=0.6, label='Target f')
            # Vertical dashed line at matching parameter (if in range)
            if have_match and x_val is not None:
                ax.axvline(x=x_val, color='r', linestyle='--', alpha=0.6)
                ax.plot([x_val], [f0_val], 'ro', alpha=0.7)
            st.pyplot(fig)

            # Downloads of the figure and data
            png_buf = BytesIO(); pdf_buf = BytesIO()
            fig.savefig(png_buf, format='png', bbox_inches='tight', dpi=300)
            fig.savefig(pdf_buf, format='pdf', bbox_inches='tight')
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button("Download PNG", data=png_buf.getvalue(), file_name=f"helmholtz_neck_{vary_param}.png", mime="image/png")
            with c2:
                st.download_button("Download PDF", data=pdf_buf.getvalue(), file_name=f"helmholtz_neck_{vary_param}.pdf", mime="application/pdf")
            with c3:
                csv_buf = BytesIO(); df.to_csv(csv_buf, index=False)
                st.download_button("Download CSV", csv_buf.getvalue(), f"helmholtz_neck_{vary_param}.csv", "text/csv")

            # Text feedback
            if not have_match:
                st.warning("Target frequency is outside the plotted range.")
            else:
                st.success(f"Closest {vary_param}: {x_val:.3f} (f0 = {f0_val:.2f} Hz)")
        else:
            st.info("Run a parameter sweep from the form to see analysis.")

with st.expander("Theory"):
    st.markdown(r"""
    **Resonance frequency formula:**
    $f_0 = k \cdot \frac{c}{2\pi} \sqrt{\frac{A}{V \cdot L_{eff}}}$
    where:
    - $c$ = speed of sound (≈343 m/s at 20°C)
    - $A$ = total hole area
    - $V$ = cavity volume
    - $L_{eff}$ = effective neck length = thickness + end correction
    - $k$ = correction factor (empiric)
    """)
    st.image("https://media.cheggcdn.com/media%2F352%2F352c4c43-1624-4466-b3f7-0854654c3ca1%2FphplUUdj3.png")

with st.expander("Calculation Notes"):
    st.markdown("""
    **Correction Factor (k) - Common Values:**
    - **0.50** - Closely spaced holes (spacing < 2×diameter)
    - **0.60** - Porous composite materials
    - **0.72** - Rectangular perforations
    - **0.92** - Multi-layer systems
    - **1.05** - Openings with debris screens
    - **1.25** - Serially coupled resonators

    **Variation Sources:**
    - Hole shape
    - Internal surface roughness

    **Reference:** Ingard (2014)
    """, unsafe_allow_html=True)

st.image("http://static1.squarespace.com/static/658043d6c66e634cdbc7a4cc/t/65b2a24c41f1487f15750d7f/1706205772677/Logo-Lydech-avec-baseline-h240.png?format=1500w")
