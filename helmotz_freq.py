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
        mode = inputs.get('mode', 'Number')
        
        # Unit conversions
        c = 20.05 * math.sqrt(273.15 + inputs['temp']) 
        D = inputs['D'] / 1000
        t = inputs['t'] / 1000
        d = inputs['d'] / 1000
        L = inputs['L'] / 1000
        # Material area calculations
        material_area = math.pi * (D / 2) ** 2
        hole_area = math.pi * (d / 2) ** 2
        
        # Calculate number of holes
        if mode == 'Number':
            N = inputs['N']
        elif mode == 'Density':
            N = int(inputs['density'] * (material_area * 10000))
        elif mode == 'OA%':
            N = int((inputs['OA'] / 100 * material_area) / hole_area)
        else:  # Spacing
            spacing_mm = inputs['spacing']
            spacing_cm = spacing_mm / 10
            density = 1 / (spacing_cm ** 2)
            N = int(density * (material_area * 10000))
            N = max(N, 1)

        # Final calculations
        A = N * hole_area
        V = material_area * L
        Leff = t
        
        if A * V * Leff == 0:
            raise ValueError("Invalid parameters combination")
            
        f0 = inputs['k'] * (c / (2 * math.pi)) * math.sqrt(A / (V * Leff))
        
        # Calculate OA% for Spacing mode
        if mode == 'Spacing':
            OA_percent = ((math.pi * (d * 1000) ** 2) / (4 * (spacing_mm ** 2))) * 100
        else:
            OA_percent = (A / material_area) * 100
        
        return {
            'f0': f0,
            'OA%': OA_percent,
            'density': N / (material_area * 10000),
            'spacing': math.sqrt(1 / (N / (material_area * 10000))) * 10 if N else 0,
            'N': N
        }
        
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return None
        
        # Final calculations
        A = N * hole_area
        V = material_area * L
        Leff = t
        
        if A * V * Leff == 0:
            raise ValueError("Invalid parameters combination")
            
        f0 = inputs['k'] * (c / (2 * math.pi)) * math.sqrt(A / (V * Leff))
        
        return {
            'f0': f0,
            'OA%': (A / material_area) * 100,
            'density': N / (material_area * 10000),
            'spacing': math.sqrt(1 / (N / (material_area * 10000))) * 10 if N else 0,
            'N': N
        }
        
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return None

# Interface

with st.sidebar:
    st.header("Main Parameters")
    inputs = {
        'temp': st.number_input("Temperature (°C)", -20.0, 250.0, 20.0),
        'D': st.number_input("Material diameter (mm)", 5.0, 1000.0, 100.0),
        't': st.number_input("Material thickness (mm)", 0.05, 50.0, 1.0),
        'd': st.number_input("Hole diameter (mm)", 0.1, 50.0, 5.0),
        'L': st.number_input("Air gap (mm)", 0.01, 100.0, 10.0),
        'k': st.number_input("Correction factor (k)", 0.1, 2.0, 1.0, 0.1)
    }
    
    calc_mode = st.radio("Calculation mode:", 
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

    st.header("Parameter Analysis")
    vary_params = [
        "None", "Temperature", "Material thickness", 
        "Hole diameter", "Air gap", "Material diameter",
        "Hole density", "Number of holes", "OA%", 
        "Hole spacing", "Correction factor"
    ]
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
            cols[1].metric("Number of Holes", int(metrics['N']))
            
            st.markdown("**Secondary Parameters:**")
            cols2 = st.columns(3)
            cols2[0].metric("Open Area", f"{metrics['OA%']:.2f}%")
            cols2[1].metric("Hole Density", f"{metrics['density']:.2f}/cm²")
            cols2[2].metric("Hole Spacing", f"{metrics['spacing']:.2f} mm")
    else:
        progress = st.progress(0)
        for i, val in enumerate(param_range):
            current = base_inputs.copy()
            
            # Update varying parameter
            if vary_param == "Temperature":
                current['temp'] = val
            elif vary_param == "Material thickness":
                current['t'] = val
            elif vary_param == "Hole diameter":
                current['d'] = val
            elif vary_param == "Air gap":
                current['L'] = val
            elif vary_param == "Material diameter":
                current['D'] = val
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
            
            
            # Create plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(df['x'], df['f0'], 'b-', lw=2, label='Resonance Frequency')
            
            # Configuration du graphique
            title = f"Helmholtz Resonance Frequency vs. {vary_param}"
            ax.set_title(title, fontsize=15, pad=20)
            ax.set_xlabel(vary_param, fontsize=12)
            ax.set_ylabel("Frequency (Hz)", fontsize=12)
            ax.grid(True, alpha=0.4)
            
            # Légende améliorée
            density = f"{df['density'].iloc[-1]:.2e}" if df['density'].iloc[-1] < 0.05 else f"{df['density'].iloc[-1]:.2f}"
            text = f"""Final Parameters:
- Density: {density}/cm²
- Holes: {int(df['N'].iloc[-1])}
- Hole diameter: {inputs['d']} mm
- Material thickness: {inputs['t']} mm
- Air gap: {inputs['L']} mm
- OA%: {df['OA%'].iloc[-1]:.2f}%"""
            
            annotation = ax.annotate(text, 
                                    xy=(0.60, 0.85), 
                                    xycoords='axes fraction',
                                    ha='left', 
                                    va='top',
                                    fontsize=12,
                                    fontfamily='monospace',
                                    bbox=dict(boxstyle='round', 
                                              facecolor='white', 
                                              alpha=0.8,
                                              edgecolor='lightgray'))
            
            # Use mplcursors to make the annotation interactive
            cursor = mplcursors.cursor(annotation)
            cursor.connect("add", lambda sel: sel.annotation.set_text(text))
            
            # Préparer les buffers en dehors des boutons
            png_buf = BytesIO()
            pdf_buf = BytesIO()
            fig.savefig(png_buf, format='png', bbox_inches='tight', dpi=300)
            fig.savefig(pdf_buf, format='pdf', bbox_inches='tight')
            st.session_state['csv'] = df.to_csv(index=False).encode()
            st.session_state['png_buf'] = png_buf
            st.session_state['pdf_buf'] = pdf_buf
            
            # Afficher le plot
            st.pyplot(fig)
                        
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    label="Download PNG",
                    data=st.session_state['png_buf'].getvalue(),
                    file_name=f"helmholtz_{vary_param}.png",
                    mime="image/png"
                )
            
            with col2:
                st.download_button(
                    label="Download PDF",
                    data=st.session_state['pdf_buf'].getvalue(),
                    file_name=f"helmholtz_{vary_param}.pdf",
                    mime="application/pdf"
                )
            
            with col3:
                st.download_button(
                    "Download CSV",
                    st.session_state['csv'],
                    f"helmholtz_{vary_param}.csv",
                    "text/csv"
                )
st.title("Helmholtz Resonance Calculator")
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
    - $L_{eff}$ = effective neck length = thickness + 0.8 $$\\cdot \\phi$$ (in theory, with small thickness,  $L_{eff}$ = thickness is used)
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
