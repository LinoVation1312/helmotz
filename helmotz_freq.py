import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
import mplcursors

st.set_page_config(page_title="Helmholtz Resonance Calculator", page_icon="https://images.squarespace-cdn.com/content/v1/658043d6c66e634cdbc7a4cc/8b08c99b-d2f0-4e8d-acfd-a91b08c6a4ed/Logo-Lydech-avec-baseline-h240.png?format=1500w",layout="centered")

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

        # Calculate material area
        material_area = math.pi * (D / 2) ** 2  # m²
        
        # Calculate volume and area based on selected modes
        if volume_mode == 'Standard':
            L = inputs['L'] / 1000  # mm to m
            V = material_area * L  # m³
        else:  # Direct Volume
            V = inputs['V'] / 1000  # L to m³
        
        if hole_mode == 'Standard':
            d = inputs['d'] / 1000  # mm to m
            hole_area = math.pi * (d / 2) ** 2  # m²
            
            # Calculate number of holes
            if calc_mode == 'Number':
                N = inputs['N']
            elif calc_mode == 'Density':
                N = int(inputs['density'] * (material_area * 10000))
            elif calc_mode == 'OA%':
                N = int((inputs['OA'] / 100 * material_area) / hole_area)
            else:  # Spacing
                spacing_mm = inputs['spacing']
                spacing_cm = spacing_mm / 10
                density = 1 / (spacing_cm ** 2)
                N = int(density * (material_area * 10000))
                N = max(N, 1)
                
            A = N * hole_area  # m²
            Leff = t + 1.7 * d / 2  # effective length with correction
            
        else:  # Direct Input
            A = inputs['A']  # m²
            Leff = inputs['Leff'] / 1000  # mm to m
            N = 0  # Not applicable for direct input
            d = 0  # Not applicable for direct input
        
        if A * V * Leff == 0:
            raise ValueError("Invalid parameters combination")

        f0 = inputs['k'] * (c / (2 * math.pi)) * math.sqrt(A / (V * Leff))
        
        # Calculate OA% based on mode
        if hole_mode == 'Standard':
            if calc_mode == 'Spacing':
                spacing_mm = inputs['spacing']
                OA_percent = ((math.pi * (d * 1000) ** 2) / (4 * (spacing_mm ** 2))) * 100
            else:
                OA_percent = (A / material_area) * 100
            
            density = N / (material_area * 10000)
            spacing = math.sqrt(1 / (N / (material_area * 10000))) * 10 if N else 0
        else:  # Direct Input
            OA_percent = (A / material_area) * 100 if material_area > 0 else 0
            density = 0  # Not applicable for direct input
            spacing = 0  # Not applicable for direct input

        return {
            'f0': f0,
            'OA%': OA_percent,
            'density': density,
            'spacing': spacing,
            'N': N,
            'V': V * 1000,  # m³ to L
            'A': A,  # m²
            'Leff': Leff * 1000  # m to mm
        }

    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return None

# Interface
st.title("Helmholtz Resonance Calculator")

with st.sidebar:
    st.header("Main Parameters")
    
    # Common parameters
    inputs = {
        'temp': st.number_input("Temperature (°C)", -20.0, 250.0, 20.0),
        'D': st.number_input("Material diameter (mm)", 5.0, 1000.0, 100.0),
        't': st.number_input("Material thickness (mm)", 0.05, 50.0, 1.0),
        'k': st.number_input("Correction factor (k)", 0.1, 2.0, 1.0, 0.1)
    }
    
    # Volume mode selection
    volume_mode = st.radio("Volume calculation:", ["Standard", "Direct Input"])
    inputs['volume_mode'] = volume_mode
    
    if volume_mode == "Standard":
        inputs['L'] = st.number_input("Air gap (mm)", 0.01, 200.0, 10.0)
    else:  # Direct Input
        inputs['V'] = st.number_input("Volume (L)", 0.001, 100.0, 0.078, format="%.3f", 
                                      help="Direct input of resonator volume in liters")
    
    # Hole mode selection
    hole_mode = st.radio("Hole calculation:", ["Standard", "Direct Input"])
    inputs['hole_mode'] = hole_mode
    
    if hole_mode == "Standard":
        inputs['d'] = st.number_input("Hole diameter (mm)", 0.1, 50.0, 5.0)
        
        calc_mode = st.radio("Hole calculation mode:",
                          ["Number", "Density", "OA%", "Spacing"])
        inputs['mode'] = calc_mode

        if calc_mode == "Number":
            inputs['N'] = st.number_input("Number of holes", 1, 10000, 100)
        elif calc_mode == "Density":
            inputs['density'] = st.number_input("Holes/cm²", 0.001, 100.0, 10.0)
        elif calc_mode == "OA%":
            inputs['OA'] = st.number_input("Open Area (%)", 0.1, 100.0, 5.0)
        else:
            inputs['spacing'] = st.number_input("Hole spacing (mm)", 0.1, 100.0, 10.0)
    else:  # Direct Input
        inputs['A'] = st.number_input("Total hole area (m²)", 0.000001, 1.0, 0.00196, format="%.6f",
                                     help="Direct input of total perforation area in square meters")
        inputs['Leff'] = st.number_input("Effective length (mm)", 0.01, 100.0, 5.0,
                                       help="Direct input of effective neck length (material thickness + end correction)")

    st.header("Parameter Analysis")
    vary_params = [
        "None", "Temperature", "Material thickness", "Material diameter",
        "Correction factor"
    ]
    
    # Add parameters based on selected modes
    if hole_mode == "Standard":
        vary_params.extend(["Hole diameter", "Number of holes", "Hole density", "OA%", "Hole spacing"])
    else:
        vary_params.extend(["Total hole area", "Effective length"])
        
    if volume_mode == "Standard":
        vary_params.append("Air gap")
    else:
        vary_params.append("Volume")
    
    vary_param = st.selectbox("Vary parameter:", vary_params)

    param_range = None
    if vary_param != "None":
        st.subheader("Variation Range")
        min_val = st.number_input("Min value", value=1.0)
        max_val = st.number_input("Max value", value=10.0)
        steps = st.number_input("Steps", 10, 1000, 50)
        param_range = np.linspace(min_val, max_val, steps)

if st.sidebar.button("Calculate"):
    results = []
    base_inputs = inputs.copy()

    if vary_param == "None":
        metrics = calculate_metrics(base_inputs)
        if metrics:
            st.subheader("Results")
            cols = st.columns(2)
            cols[0].metric("Resonance Frequency", f"{metrics['f0']:.1f} Hz")
            
            if inputs['hole_mode'] == 'Standard':
                cols[1].metric("Number of Holes", int(metrics['N']))
            
            st.markdown("**Parameters:**")
            
            if inputs['volume_mode'] == 'Standard':
                vol_text = f"Air gap: {inputs['L']:.2f} mm"
            else:
                vol_text = f"Volume: {metrics['V']:.3f} L"
                
            if inputs['hole_mode'] == 'Standard':
                hole_text = f"Open Area: {metrics['OA%']:.2f}%"
                if inputs['mode'] != 'OA%':
                    hole_text += f" | Density: {metrics['density']:.2f}/cm²"
                if inputs['mode'] != 'Spacing':
                    hole_text += f" | Spacing: {metrics['spacing']:.2f} mm"
            else:
                hole_text = f"Total hole area: {metrics['A']:.6f} m² | Leff: {metrics['Leff']:.2f} mm"
            
            st.info(f"{vol_text} | {hole_text}")
    else:
        progress = st.progress(0)
        for i, val in enumerate(param_range):
            current = base_inputs.copy()

            # Update varying parameter
            if vary_param == "Temperature":
                current['temp'] = val
            elif vary_param == "Material thickness":
                current['t'] = val
            elif vary_param == "Material diameter":
                current['D'] = val
            elif vary_param == "Air gap":
                current['L'] = val
            elif vary_param == "Volume":
                current['V'] = val
            elif vary_param == "Hole diameter":
                current['d'] = val
            elif vary_param == "Total hole area":
                current['A'] = val
            elif vary_param == "Effective length":
                current['Leff'] = val
            elif vary_param == "Hole density":
                current['density'] = val
                current['mode'] = "Density"
            elif vary_param == "Number of holes":
                current['N'] = int(val)
                current['mode'] = "Number"
            elif vary_param == "OA%":
                current['OA'] = val
                current['mode'] = "OA%"
            elif vary_param == "Hole spacing":
                current['spacing'] = val
                current['mode'] = "Spacing"
            elif vary_param == "Correction factor":
                current['k'] = val

            metrics = calculate_metrics(current)
            if metrics:
                results.append({'x': val, 'f0': metrics['f0'], **metrics})
            progress.progress((i + 1) / len(param_range))

        if results:
            df = pd.DataFrame(results)

            st.session_state['analysis_df'] = df
            st.session_state['vary_param'] = vary_param
            st.session_state['base_inputs'] = base_inputs


if 'analysis_df' in st.session_state and 'vary_param' in st.session_state:
    df = st.session_state['analysis_df']
    vary_param = st.session_state['vary_param']
    base_inputs = st.session_state['base_inputs']

    # Création du plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df['x'], df['f0'], 'b-', lw=2, label='Resonance Frequency')

    title = f"Helmholtz Resonance Frequency vs. {vary_param}"
    ax.set_title(title, fontsize=15, pad=20)
    ax.set_xlabel(vary_param, fontsize=12)
    ax.set_ylabel("Frequency (Hz)", fontsize=12)
    ax.grid(True, alpha=0.4)

    # Préparer la légende basée sur le mode
    if base_inputs['hole_mode'] == 'Standard':
        if 'density' in df and df['density'].iloc[-1] > 0:
            density = f"{df['density'].iloc[-1]:.2e}" if df['density'].iloc[-1] < 0.05 else f"{df['density'].iloc[-1]:.2f}"
            hole_info = f"- Hole Density: {density}/cm²\n- Hole diameter: {base_inputs.get('d', 0)} mm"
        else:
            hole_info = ""
    else:
        hole_info = f"- Total hole area: {df['A'].iloc[-1]:.6f} m²\n- Leff: {df['Leff'].iloc[-1]:.2f} mm"
    
    if base_inputs['volume_mode'] == 'Standard':
        volume_info = f"- Air gap: {base_inputs.get('L', 0)} mm"
    else:
        volume_info = f"- Volume: {df['V'].iloc[-1]:.3f} L"
    
    text = f"""Final Parameters:
{hole_info}
- Material thickness: {base_inputs['t']} mm
{volume_info}"""

    if base_inputs['hole_mode'] == 'Standard' and 'OA%' in df:
        text += f"\n- OA%: {df['OA%'].iloc[-1]:.2f}%"

    annotation_position = (0.05, 0.95)
    if any(df['f0'] > df['f0'].iloc[-1] * 1.1):  
        annotation_position = (0.60, 0.15)  

    annotation = ax.annotate(
        text,
        xy=annotation_position,
        xycoords='axes fraction',
        ha='left',
        va='top',
        fontsize=12,
        fontfamily='monospace',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='lightgray')
    )

    # Widget de saisie de la fréquence
    target_freq = st.number_input(
        "Enter target frequency (Hz) [0-10000]:",
        min_value=0.0,
        max_value=10000.0,
        value=1000.0,
        step=100.0
    )

    # Vérification de la plage
    min_f0 = df['f0'].min()
    max_f0 = df['f0'].max()

    if target_freq < min_f0 or target_freq > max_f0:
        st.warning("⚠️ Target frequency is out of the current graph range")
    else:
        # Recherche de la valeur la plus proche
        idx = np.abs(df['f0'] - target_freq).argmin()
        closest_row = df.iloc[idx]
        x_val = closest_row['x']
        f0_val = closest_row['f0']

        # Ajout des marqueurs
        ax.axvline(x=x_val, color='r', linestyle='--', alpha=0.7)
        ax.axhline(y=f0_val, color='r', linestyle='--', alpha=0.7)
        ax.plot(x_val, f0_val, 'ro', markersize=8)

        # Affichage de la valeur
        st.success(f"**Corresponding {vary_param}:** {x_val:.2f} (Exact frequency: {f0_val:.2f} Hz)")

    # Afficher le plot
    st.pyplot(fig)

    # Gestion des téléchargements
    png_buf = BytesIO()
    pdf_buf = BytesIO()
    fig.savefig(png_buf, format='png', bbox_inches='tight', dpi=300)
    fig.savefig(pdf_buf, format='pdf', bbox_inches='tight')

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="Download PNG",
            data=png_buf.getvalue(),
            file_name=f"helmholtz_{vary_param}.png",
            mime="image/png"
        )

    with col2:
        st.download_button(
            label="Download PDF",
            data=pdf_buf.getvalue(),
            file_name=f"helmholtz_{vary_param}.pdf",
            mime="application/pdf"
        )

    with col3:
        csv_buf = BytesIO()
        df.to_csv(csv_buf, index=False)
        st.download_button(
            "Download CSV",
            csv_buf.getvalue(),
            f"helmholtz_{vary_param}.csv",
            "text/csv"
        )

with st.expander("Theory"):
    st.markdown("""
    **Resonance frequency formula:**
    $$
    f_0 = k \\cdot \\frac{c}{2\\pi} \\sqrt{\\frac{A}{V \\cdot L_{eff}}}
    $$
    where:
    - $c$ = speed of sound (≈343 m/s at 20°C)
    - $A$ = total hole area
    - $V$ = cavity volume
    - $L_{eff}$ = effective neck length = thickness + 0.8 $$\\cdot \\phi$$
    - $k$ = correction factor (empiric)
    """)
    st.image("https://media.cheggcdn.com/media%2F352%2F352c4c43-1624-4466-b3f7-0854654c3ca1%2FphplUUdj3.png")

with st.expander("Calculation Notes"):
    st.markdown("""
    **Correction Factor (k) - Common Values:**
    - **0.50** - Closely spaced holes (spacing < 2×diameter) with aerodynamic interactions
    - **0.60** - Porous composite materials (acoustic foam + rigid plate)
    - **0.72** - Rectangular perforations (2:1 aspect ratio)
    - **0.92** - Multi-layer systems (2 parallel plates)
    - **1.05** - Openings with debris screens
    - **1.25** - Serially coupled resonators

    **Variation Sources:**
    - Hole shape (round vs. slot vs. hexagonal ...)
    - Internal surface roughness

    **Experimental Reference:**
    Values derived from
    [*Eﬀective conditions for the reﬂection of an acoustic wave by low-porosity perforated plates* (Ingard, 2014)](https://www.academia.edu/83400811/Effective_conditions_for_the_reflection_of_an_acoustic_wave_by_low-porosity_perforated_plates)
    """, unsafe_allow_html=True)

st.markdown("<br><br><br><br><br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

st.image("http://static1.squarespace.com/static/658043d6c66e634cdbc7a4cc/t/65b2a24c41f1487f15750d7f/1706205772677/Logo-Lydech-avec-baseline-h240.png?format=1500w")
