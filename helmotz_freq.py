import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

st.set_page_config(page_title="Helmholtz Resonance Frequency Calculator", layout="centered")

def calculate_holes_from_spacing(material_diameter_mm, d_spacing_mm):
    """Calcule le nombre de trous pour un espacement donné en arrangement carré dans un cercle"""
    D = material_diameter_mm
    d = d_spacing_mm
    radius = D / 2.0
    max_holes_per_axis = int(D // d)
    start = -((max_holes_per_axis - 1) * d) / 2.0
    x_positions = [start + i*d for i in range(max_holes_per_axis)]
    y_positions = x_positions.copy()
    total_holes = 0
    
    for x in x_positions:
        for y in y_positions:
            if math.sqrt(x**2 + y**2) <= radius:
                total_holes += 1
    return total_holes

def calculate_frequency(temperature, thickness_mm, hole_diameter_mm, number_of_holes, material_diameter_mm, airgap_mm, k):
    try:
        # Conversion des unités
        c = 20.05 * math.sqrt(273.15 + temperature)  # Vitesse du son (m/s)
        thickness = thickness_mm / 1000  # Épaisseur (m)
        hole_diameter = hole_diameter_mm / 1000  # Diamètre des trous (m)
        material_diameter = material_diameter_mm / 1000  # Diamètre matériau (m)
        airgap = airgap_mm / 1000  # Épaisseur cavité (m)

        # Calculs des aires
        material_area = math.pi * (material_diameter/2)**2
        hole_area = math.pi * (hole_diameter/2)**2
        total_hole_area = number_of_holes * hole_area
        
        # Volume de la cavité
        cavity_volume = material_area * airgap

        # Longueur effective
        end_correction = 0.85 * (hole_diameter/2)
        effective_length = thickness + 2 * end_correction

        # Fréquence de résonance
        if total_hole_area > 0 and cavity_volume > 0 and effective_length > 0:
            frequency = k * (c / (2 * math.pi)) * math.sqrt(total_hole_area / (cavity_volume * effective_length))
            return round(frequency, 2)
        else:
            raise ValueError("Paramètres manquants ou invalides")
    
    except Exception as e:
        st.error(f"Erreur de calcul: {str(e)}")
        return None

# Interface utilisateur
st.title("Calculateur de Fréquence de Résonance Helmholtz")
with st.expander("Théorie"):
    st.image("https://media.cheggcdn.com/media%2F352%2F352c4c43-1624-4466-b3f7-0854654c3ca1%2FphplUUdj3.png")
    st.markdown("""
    **Formule principale:**
    
    $$
    f = k \\cdot \\frac{c}{2\\pi} \\cdot \\sqrt{\\frac{A}{V \\cdot L_{\\text{eff}}}
    $$

    où:
    - $c = 20.05 \\cdot \\sqrt{T_{\\text{K}}}$ (vitesse du son)
    - $A$ = surface totale des trous
    - $V$ = volume de la cavité
    - $L_{\\text{eff}}$ = épaisseur + correction de bord
    - $k$ = coefficient de correction
    """)

with st.sidebar:
    st.header("Paramètres d'entrée")
    temperature = st.number_input("Température (°C)", -50.0, 100.0, 20.0)
    thickness_mm = st.number_input("Épaisseur matériau (mm)", 0.1, 100.0, 1.0)
    hole_diameter_mm = st.number_input("Diamètre des trous (mm)", 0.1, 50.0, 5.0)
    material_diameter_mm = st.number_input("Diamètre matériau (mm)", 1.0, 1000.0, 100.0)
    airgap_mm = st.number_input("Épaisseur cavité (mm)", 0.1, 100.0, 10.0)
    k = st.number_input("Coefficient de correction (k)", 0.1, 2.0, 1.0, 0.1)
    
    hole_method = st.radio("Mode de calcul", ["Nombre de trous", "Densité de trous", "Espacement des trous"])
    
    if hole_method == "Nombre de trous":
        number_of_holes = st.number_input("Nombre de trous", 1, 1000, 10)
    elif hole_method == "Densité de trous":
        density = st.number_input("Densité (trous/cm²)", 0.1, 100.0, 5.0)
    else:
        d_spacing_mm = st.number_input("Espacement entre trous (mm)", 0.1, 1000.0, 10.0)

    # Paramètre variable
    vary_param = st.selectbox("Paramètre variable", ["Aucun", "Température", "Épaisseur", "Diamètre trous", "Épaisseur cavité", "Diamètre matériau"])
    
    param_range = None
    if vary_param != "Aucun":
        st.subheader("Plage de variation")
        min_val = st.number_input("Valeur minimale", 0.0, 1000.0, 0.0)
        max_val = st.number_input("Valeur maximale", 0.0, 1000.0, 100.0)
        steps = st.number_input("Nombre de points", 10, 1000, 100)
        param_range = np.linspace(min_val, max_val, steps)

if st.sidebar.button("Calculer"):
    # Calcul des informations communes
    material_area_cm2 = math.pi * (material_diameter_mm / 20)**2
    material_area_mm2 = math.pi * (material_diameter_mm / 2)**2
    
    if hole_method == "Densité de trous":
        number_of_holes = int(density * material_area_cm2)
    elif hole_method == "Espacement des trous":
        number_of_holes = calculate_holes_from_spacing(material_diameter_mm, d_spacing_mm)
    
    # Calculs des métriques
    density = number_of_holes / material_area_cm2 if material_area_cm2 > 0 else 0
    hole_area_mm2 = math.pi * (hole_diameter_mm/2)**2
    total_hole_area_mm2 = number_of_holes * hole_area_mm2
    OA_percentage = (total_hole_area_mm2 / material_area_mm2) * 100 if material_area_mm2 > 0 else 0
    
    if hole_method != "Espacement des trous":
        spacing_d_mm = math.sqrt((material_area_cm2 * 100) / number_of_holes) if number_of_holes > 0 else 0
    else:
        spacing_d_mm = d_spacing_mm

    # Affichage des résultats
    st.subheader("Résultats")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre de trous", f"{number_of_holes}")
    with col2:
        st.metric("Densité (trous/cm²)", f"{density:.2f}")
    with col3:
        st.metric("Espacement (mm)", f"{spacing_d_mm:.2f}")
    
    st.metric("Ouverture Acoustique (OA)", f"{OA_percentage:.2f}%")

    # Suite du calcul principal...
    # [Le reste du code original pour les calculs de fréquence et visualisation]
