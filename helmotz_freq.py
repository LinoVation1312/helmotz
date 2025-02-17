import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Helmholtz Resonance Calculator", layout="centered")

def calculate_holes_from_spacing(D_mm, spacing_mm):
    """Calculate number of holes in square arrangement within a circle"""
    radius = D_mm / 2
    grid_points = int(D_mm // spacing_mm)
    start = -((grid_points - 1) * spacing_mm) / 2
    positions = [start + i*spacing_mm for i in range(grid_points)]
    return sum(1 for x in positions for y in positions if math.hypot(x, y) <= radius)

def calculate_metrics(inputs):
    """Calculate all acoustic parameters and frequency"""
    try:
        # Convert units to meters
        c = 20.05 * math.sqrt(273.15 + inputs['temp'])
        D = inputs['D'] / 1000
        t = inputs['t'] / 1000
        d = inputs['d'] / 1000
        L = inputs['L'] / 1000
        
        # Material area calculations
        material_area = math.pi * (D/2)**2
        hole_area = math.pi * (d/2)**2
        
        # Calculate number of holes based on input mode
        if inputs['mode'] == 'Number':
            N = inputs['N']
        elif inputs['mode'] == 'Density':
            N = int(inputs['density'] * (material_area * 10000))  # m² to cm²
        elif inputs['mode'] == 'OA%':
            N = int((inputs['OA']/100 * material_area) / hole_area)
        else:  # Spacing mode
            N = calculate_holes_from_spacing(inputs['D'], inputs['spacing'])

        # Final calculations
        A = N * hole_area
        V = material_area * L
        Leff = t + 2 * 0.85 * (d/2)
        
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
        st.error(f"Error: {str(e)}")
        return None

# Interface
st.title("Helmholtz Resonance Calculator")
with st.expander("Theory"):
    st.markdown("""
    **Resonance frequency formula:**
    $$
    f_0 = \\frac{k}{2\\pi} \\sqrt{\\frac{A}{V \\cdot L_{eff}}}
    $$
    where:
    - $A$: Total hole area ($m^2$)
    - $V$: Cavity volume ($m^3$)
    - $L_{eff}$: Effective neck length ($t + 2 \\times 0.85r$)
    - $k$: Empirical correction factor
    """)

with st.sidebar:
    st.header("Main Parameters")
    inputs = {
        'temp': st.number_input("Temperature (°C)", -20.0, 100.0, 20.0),
        'D': st.number_input("Material diameter (mm)", 10.0, 1000.0, 100.0),
        't': st.number_input("Material thickness (mm)", 0.1, 50.0, 1.0),
        'd': st.number_input("Hole diameter (mm)", 0.1, 50.0, 5.0),
        'L': st.number_input("Air gap (mm)", 0.1, 100.0, 10.0),
        'k': st.number_input("Correction factor (k)", 0.1, 2.0, 1.0, 0.1)
    }
    
    calc_mode = st.radio("Calculation mode:", 
                        ["Number", "Density", "OA%", "Spacing"])
    
    if calc_mode == "Number":
        inputs['N'] = st.number_input("Number of holes", 1, 10000, 100)
    elif calc_mode == "Density":
        inputs['density'] = st.number_input("Holes/cm²", 0.1, 100.0, 10.0)
    elif calc_mode == "OA%":
        inputs['OA'] = st.number_input("Open Area (%)", 0.1, 100.0, 5.0)
    else:
        inputs['spacing'] = st.number_input("Hole spacing (mm)", 0.1, 100.0, 10.0)

    st.header("Parameter Analysis")
    vary_param = st.selectbox("Vary parameter:", ["None", "Temperature", "Thickness",
                                                "Hole diameter", "Air gap", 
                                                "Material diameter", "Hole density",
                                                "Number of holes", "OA%", 
                                                "Hole spacing"])
    
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
            cols = st.columns(4)
            cols[0].metric("Resonance Frequency", f"{metrics['f0']:.1f} Hz")
            cols[1].metric("Open Area", f"{metrics['OA%']:.1f}%")
            cols[2].metric("Hole Density", f"{metrics['density']:.1f}/cm²")
            cols[3].metric("Hole Spacing", f"{metrics['spacing']:.1f} mm")
    else:
        progress = st.progress(0)
        for i, val in enumerate(param_range):
            current = base_inputs.copy()
            
            # Update varying parameter
            if vary_param == "Temperature":
                current['temp'] = val
            elif vary_param == "Thickness":
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
            else:  # Hole spacing
                current['spacing'] = val
                current['mode'] = "Spacing"
            
            metrics = calculate_metrics(current)
            if metrics:
                results.append({'x': val, 'f0': metrics['f0'], **metrics})
            progress.progress((i+1)/len(param_range))
        
        if results:
            df = pd.DataFrame(results)
            
            # Create plot
            fig, ax = plt.subplots(figsize=(10,6))
            ax.plot(df['x'], df['f0'], 'b-', lw=2)
            ax.set_xlabel(vary_param)
            ax.set_ylabel("Resonance Frequency (Hz)")
            ax.grid(True)
            
            # Add annotations
            text = f"""
            Final values:
            - OA%: {df['OA%'].iloc[-1]:.1f}%
            - Density: {df['density'].iloc[-1]:.1f}/cm²
            - Spacing: {df['spacing'].iloc[-1]:.1f} mm
            - Holes: {int(df['N'].iloc[-1])}
            """
            ax.annotate(text, xy=(0.98, 0.5), xycoords='axes fraction',
                       ha='right', va='center', fontsize=10,
                       bbox=dict(boxstyle='round', alpha=0.2))
            
            st.pyplot(fig)
            
            # Export options
            if st.button("Download Data (CSV)"):
                csv = df.to_csv(index=False).encode()
                st.download_button("Download", csv, "data.csv", "text/csv")

with st.expander("Calculation Notes"):
    st.markdown("""
    **Key relationships:**
    - OA% = (Total Hole Area / Material Area) × 100
    - Density = 100 / (spacing²) [holes/cm²]
    - Spacing = 10 / sqrt(density) [mm]
    """)
