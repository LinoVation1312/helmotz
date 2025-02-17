import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

st.set_page_config(page_title="Helmholtz Resonance Calculator", layout="centered")

def calculate_holes_from_spacing(material_diameter_mm, d_spacing_mm):
    """Calculate number of holes in square arrangement within a circle"""
    D = material_diameter_mm
    d = d_spacing_mm
    radius = D / 2.0
    max_holes_per_axis = int(D // d)
    start = -((max_holes_per_axis - 1) * d) / 2.0
    positions = [start + i*d for i in range(max_holes_per_axis)]
    total_holes = 0
    
    for x in positions:
        for y in positions:
            if math.sqrt(x**2 + y**2) <= radius:
                total_holes += 1
    return total_holes

def calculate_metrics(params):
    """Calculate all acoustic metrics without frequency"""
    try:
        # Convert units
        material_area_mm2 = math.pi * (params['material_diameter_mm']/2)**2
        material_area_cm2 = material_area_mm2 / 100
        
        # Hole calculations
        hole_area_mm2 = math.pi * (params['hole_diameter_mm']/2)**2
        total_hole_area_mm2 = params['number_of_holes'] * hole_area_mm2
        
        # Acoustic opening percentage
        OA_percentage = (total_hole_area_mm2 / material_area_mm2) * 100 if material_area_mm2 > 0 else 0
        
        # Density and spacing calculations
        if params['calculation_mode'] == "Hole Spacing":
            # Exact density calculation for square pattern
            density = 100 / (params['d_spacing_mm']**2)  # Exact 1/cm² conversion
            spacing = params['d_spacing_mm']
        else:
            density = params['number_of_holes'] / material_area_cm2 if material_area_cm2 > 0 else 0
            spacing = math.sqrt(100 / density) if density > 0 else 0  # mm between holes

        return {
            'OA%': OA_percentage,
            'density': density,
            'spacing': spacing,
            'holes': params['number_of_holes']
        }
    
    except Exception as e:
        st.error(f"Calculation error: {str(e)}")
        return None

# User interface
st.title("Acoustic Perforation Calculator")
with st.expander("Theory"):
    st.image("https://media.cheggcdn.com/media%2F352%2F352c4c43-1624-4466-b3f7-0854654c3ca1%2FphplUUdj3.png")
    st.markdown("""
    **Key metrics:**
    - OA% (Open Area): Total hole area / Material area × 100
    - Density: Holes per cm²
    - Spacing: Distance between hole centers (mm)
    """)

with st.sidebar:
    st.header("Input Parameters")
    material_diameter_mm = st.number_input("Material diameter (mm)", 1.0, 1000.0, 100.0)
    hole_diameter_mm = st.number_input("Hole diameter (mm)", 0.1, 50.0, 5.0)
    
    calculation_mode = st.radio("Calculation Mode", 
                               ["Number of Holes", "Hole Density", "Hole Spacing"])
    
    if calculation_mode == "Number of Holes":
        number_of_holes = st.number_input("Number of holes", 1, 10000, 100)
    elif calculation_mode == "Hole Density":
        target_density = st.number_input("Target density (holes/cm²)", 0.1, 1000.0, 10.0)
    else:
        d_spacing_mm = st.number_input("Center-to-center spacing (mm)", 0.1, 100.0, 2.0)

    # Variable parameter analysis
    vary_param = st.selectbox("Parameter analysis", 
                             ["None", "Hole diameter", "Spacing", "Material diameter"])
    
    param_range = None
    if vary_param != "None":
        st.subheader("Variation Range")
        min_val = st.number_input("Min value", 0.1, 1000.0, 1.0)
        max_val = st.number_input("Max value", 0.1, 1000.0, 10.0)
        steps = st.number_input("Data points", 10, 1000, 50)
        param_range = np.linspace(min_val, max_val, steps)

if st.sidebar.button("Calculate"):
    # Calculate base parameters
    params = {
        'material_diameter_mm': material_diameter_mm,
        'hole_diameter_mm': hole_diameter_mm,
        'calculation_mode': calculation_mode,
        'number_of_holes': 0  # Initialize
    }

    # Calculate initial hole count
    if calculation_mode == "Number of Holes":
        params['number_of_holes'] = number_of_holes
    elif calculation_mode == "Hole Density":
        material_area_cm2 = (math.pi * (material_diameter_mm/20)**2)
        params['number_of_holes'] = int(target_density * material_area_cm2)
    else:  # Hole Spacing
        params['d_spacing_mm'] = d_spacing_mm
        params['number_of_holes'] = calculate_holes_from_spacing(material_diameter_mm, d_spacing_mm)

    # Calculate and display metrics
    metrics = calculate_metrics(params)
    if metrics:
        st.subheader("Results")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Open Area (OA%)", f"{metrics['OA%']:.2f}%")
        with col2: st.metric("Hole density", f"{metrics['density']:.2f}/cm²")
        with col3: st.metric("Hole spacing", f"{metrics['spacing']:.2f} mm")
        with col4: st.metric("Total holes", int(metrics['holes']))

    # Parameter variation analysis
    if vary_param != "None" and param_range is not None:
        results = []
        for val in param_range:
            # Update varying parameter
            if vary_param == "Hole diameter":
                params['hole_diameter_mm'] = val
            elif vary_param == "Spacing":
                params['d_spacing_mm'] = val
                params['number_of_holes'] = calculate_holes_from_spacing(
                    params['material_diameter_mm'], val)
            elif vary_param == "Material diameter":
                params['material_diameter_mm'] = val
                if calculation_mode == "Hole Density":
                    params['number_of_holes'] = int(target_density * 
                                                  (math.pi * (val/20)**2))

            # Calculate metrics
            metrics = calculate_metrics(params)
            if metrics:
                results.append({
                    'parameter': val,
                    'OA%': metrics['OA%'],
                    'density': metrics['density'],
                    'spacing': metrics['spacing'],
                    'holes': metrics['holes']
                })

        # Create visualizations
        if results:
            df = pd.DataFrame(results)
            
            # Create figure with subplots
            fig, axs = plt.subplots(2, 2, figsize=(12, 10))
            plt.tight_layout(pad=4.0)
            
            # Plot OA%
            axs[0,0].plot(df['parameter'], df['OA%'], 'b-')
            axs[0,0].set_title("Open Area Percentage")
            axs[0,0].set_xlabel(vary_param)
            axs[0,0].set_ylabel("OA (%)")
            axs[0,0].grid(True)
            
            # Plot Density
            axs[0,1].plot(df['parameter'], df['density'], 'r-')
            axs[0,1].set_title("Hole Density")
            axs[0,1].set_xlabel(vary_param)
            axs[0,1].set_ylabel("Holes/cm²")
            axs[0,1].grid(True)
            
            # Plot Spacing
            axs[1,0].plot(df['parameter'], df['spacing'], 'g-')
            axs[1,0].set_title("Hole Spacing")
            axs[1,0].set_xlabel(vary_param)
            axs[1,0].set_ylabel("mm")
            axs[1,0].grid(True)
            
            # Plot Total Holes
            axs[1,1].plot(df['parameter'], df['holes'], 'm-')
            axs[1,1].set_title("Total Holes")
            axs[1,1].set_xlabel(vary_param)
            axs[1,1].set_ylabel("Count")
            axs[1,1].grid(True)

            st.pyplot(fig)
            
            # Export options
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Data (CSV)", csv, 
                             "perforation_analysis.csv", "text/csv")

with st.expander("Calculation Notes"):
    st.markdown("""
    **Key Formulas:**
    - Open Area %: 
      $$ OA = \\frac{N \\cdot \\pi (d_h/2)^2}{\\pi (D_m/2)^2} \\times 100 $$
    - Hole Density (square pattern): 
      $$ \\rho = \\frac{100}{(s_{mm})^2} $$
    - Hole Spacing: 
      $$ s = \\sqrt{\\frac{100}{\\rho}} $$
    Where:
    - \( N \) = number of holes
    - \( d_h \) = hole diameter (mm)
    - \( D_m \) = material diameter (mm)
    - \( s_{mm} \) = center-to-center spacing (mm)
    - \( \\rho \) = hole density (holes/cm²)
    """)
