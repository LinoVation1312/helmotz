import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Helmholtz Resonator", layout="wide")

# Main calculation function
def calculate_frequency(temperature, thickness_mm, hole_diameter_mm, number_of_holes, material_diameter_mm, airgap_mm, k, frequency=None):
    try:
        # Unit conversions
        c = 331 + 0.6 * temperature  # Speed of sound (m/s)
        thickness = thickness_mm / 1000  # Thickness (m)
        hole_diameter = hole_diameter_mm / 1000  # Hole diameter (m)
        material_diameter = material_diameter_mm / 1000  # Material diameter (m)
        airgap = airgap_mm / 1000  # Airgap (m)

        # Calculate material area (if material_diameter is provided)
        if material_diameter_mm > 0:
            material_area = math.pi * (material_diameter / 2) ** 2  # m²
        else:
            material_area = 0  # Default value if not specified
        
        # Calculate total hole area (if hole_diameter is provided)
        if hole_diameter_mm > 0:
            hole_area = math.pi * (hole_diameter / 2) ** 2
            total_hole_area = number_of_holes * hole_area  # m²
        else:
            total_hole_area = 0  # Default value if not specified

        # Calculate cavity volume (if material_area and airgap are provided)
        if material_area > 0 and airgap_mm > 0:
            cavity_volume = material_area * airgap  # m³
        else:
            cavity_volume = 0  # Default value if not specified

        # Effective length of the neck
        if hole_diameter_mm > 0:
            end_correction = 0.85 * (hole_diameter / 2)  # End correction
            effective_length = thickness + 2 * end_correction  # m
        else:
            effective_length = thickness  # Default value if not specified

        # Calculate frequency (if cavity volume, hole area, and effective length are valid)
        if total_hole_area > 0 and cavity_volume > 0 and effective_length > 0:
            if frequency:
                return frequency
            else:
                frequency = k * (c / (2 * math.pi)) * math.sqrt(total_hole_area / (cavity_volume * effective_length))
                return round(frequency, 2)
        else:
            raise ValueError("Necessary parameters are missing or incorrect.")
    
    except Exception as e:
        st.error(f"Calculation Error: {str(e)}")
        return None

# User interface
st.title("Helmholtz Resonator Frequency Calculator")
st.image("https://media.cheggcdn.com/media%2F352%2F352c4c43-1624-4466-b3f7-0854654c3ca1%2FphplUUdj3.png")
st.markdown("""
This application calculates the resonance frequency of a Helmholtz resonator based on the provided parameters.
""")

with st.sidebar:
    st.header("Input Parameters")
    
    # Main parameters
    temperature = st.number_input("Temperature (°C)", -50.0, 100.0, 20.0)
    thickness_mm = st.number_input("Material Thickness (mm)", 0.1, 100.0, 1.0)
    hole_diameter_mm = st.number_input("Hole Diameter (mm)", 0.1, 50.0, 5.0)
    material_diameter_mm = st.number_input("Material Diameter (mm)", 1.0, 1000.0, 100.0)
    airgap_mm = st.number_input("Airgap (mm)", 0.1, 100.0, 10.0)
    k = st.number_input("Correction Coefficient (k)", 0.1, 2.0, 1.0, 0.1)
    
    # Hole calculation method
    hole_method = st.radio("Hole Calculation Method", ["Number of Holes", "Hole Density"])
    
    if hole_method == "Number of Holes":
        number_of_holes = st.number_input("Number of Holes", 1, 1000, 10)
        density = None
    else:
        density = st.number_input("Hole Density (/cm²)", 0.1, 100.0, 5.0)
        number_of_holes = None
    
    # Varying parameter
    vary_param = st.selectbox("Vary a Parameter", ["None", "Temperature", "Thickness", "Hole Diameter", "Airgap", "Material Diameter", "Frequency"])
    
    param_range = None
    if vary_param != "None":
        st.subheader("Parameter Range")
        min_val = st.number_input("Minimum Value", 0.0, 1000.0, 0.0)
        max_val = st.number_input("Maximum Value", 0.0, 1000.0, 100.0)
        steps = st.number_input("Number of Points", 10, 1000, 100)
        param_range = np.linspace(min_val, max_val, steps)

# Main calculation
if st.sidebar.button("Calculate"):
    if vary_param == "None":
        # Simple calculation
        if hole_method == "Hole Density":
            material_area_cm2 = (math.pi * (material_diameter_mm / 20)**2)  # cm²
            number_of_holes = density * material_area_cm2
        
        result = calculate_frequency(
            temperature, thickness_mm, hole_diameter_mm,
            int(number_of_holes), material_diameter_mm,
            airgap_mm, k
        )
        
        if result:
            st.success(f"**Resonance Frequency:** {result} Hz")
    
    else:
        # Calculation with varying parameter
        frequencies = []
        parameters = []
        
        for val in param_range:
            params = {
                "temperature": temperature,
                "thickness_mm": thickness_mm,
                "hole_diameter_mm": hole_diameter_mm,
                "material_diameter_mm": material_diameter_mm,
                "airgap_mm": airgap_mm,
                "k": k,
                "number_of_holes": number_of_holes
            }
            
            # Update the varying parameter
            if vary_param == "Temperature":
                params["temperature"] = val
            elif vary_param == "Thickness":
                params["thickness_mm"] = val
            elif vary_param == "Hole Diameter":
                params["hole_diameter_mm"] = val
            elif vary_param == "Airgap":
                params["airgap_mm"] = val
            elif vary_param == "Material Diameter":
                params["material_diameter_mm"] = val
            elif vary_param == "Frequency":
                params["frequency"] = val
            
            # Calculate number of holes if density is used
            if hole_method == "Hole Density":
                material_area_cm2 = (math.pi * (params["material_diameter_mm"] / 20)**2)
                params["number_of_holes"] = density * material_area_cm2
            
            # Calculate frequency
            freq = calculate_frequency(**params)
            frequencies.append(freq)
            parameters.append(val)
        
        # Display the graph
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(parameters, frequencies, 'b-')
        ax.set_xlabel(vary_param)
        ax.set_ylabel("Frequency (Hz)")
        ax.grid(True)
        st.pyplot(fig)
        
        # Export data
        df = pd.DataFrame({"Parameter": parameters, "Frequency (Hz)": frequencies})
        st.download_button(
            label="Download Data (CSV)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='resonance_data.csv',
            mime='text/csv'
        )

# Additional information
with st.expander("Theory and Correction Coefficients"):
    st.markdown("""
    **Formula used:**
    ```
    f = k * (c / (2π)) * √(A / (V * L_eff))
    where:
    - c = speed of sound (331 + 0.6*T°C)
    - A = total hole area
    - V = cavity volume
    - L_eff = thickness + end correction (0.85 * hole diameter)
    - k = correction coefficient
    ```
    """)
    
    st.markdown("""
    **Correction Coefficients:**
    - These depend on the exact geometry and boundary conditions
    - Default value for k = 1 for theoretical estimation
    - Adjust empirically to match real measurements
    """)

st.markdown("---")
st.caption("References: [A bottle of tea as a Helmholtz resonator](https://arxiv.org/abs/2108.00444) | [Resonance widths study](https://arxiv.org/abs/2203.17216)")
