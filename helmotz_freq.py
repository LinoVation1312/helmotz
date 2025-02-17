import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from io import StringIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

st.set_page_config(page_title="Calculateur de Fréquence de Résonance de Helmholtz", layout="centered")

# Fonction principale de calcul
def calculate_frequency(temperature, thickness_mm, hole_diameter_mm, number_of_holes, material_diameter_mm, airgap_mm, k):
    try:
        # Conversion des unités
        c = 331 + 0.6 * temperature  # Vitesse du son (m/s)
        thickness = thickness_mm / 1000  # Épaisseur (m)
        hole_diameter = hole_diameter_mm / 1000  # Diamètre du trou (m)
        material_diameter = material_diameter_mm / 1000  # Diamètre du matériau (m)
        airgap = airgap_mm / 1000  # Espace d'air (m)

        # Calcul de l'aire du matériau (si le diamètre est fourni)
        if material_diameter_mm > 0:
            material_area = math.pi * (material_diameter / 2) ** 2  # m²
        else:
            material_area = 0  # Valeur par défaut si non spécifié
        
        # Calcul de l'aire totale des trous (si le diamètre est fourni)
        if hole_diameter_mm > 0:
            hole_area = math.pi * (hole_diameter / 2) ** 2
            total_hole_area = number_of_holes * hole_area  # m²
        else:
            total_hole_area = 0  # Valeur par défaut si non spécifié

        # Calcul du volume de la cavité (si l'aire du matériau et l'espace d'air sont fournis)
        if material_area > 0 and airgap_mm > 0:
            cavity_volume = material_area * airgap  # m³
        else:
            cavity_volume = 0  # Valeur par défaut si non spécifié

        # Longueur effective du col
        if hole_diameter_mm > 0:
            end_correction = 0.85 * (hole_diameter / 2)  # Correction d'extrémité
            effective_length = thickness + 2 * end_correction  # m
        else:
            effective_length = thickness  # Valeur par défaut si non spécifié

        # Calcul de la fréquence (si l'aire totale des trous, le volume de la cavité et la longueur effective sont valides)
        if total_hole_area > 0 and cavity_volume > 0 and effective_length > 0:
            frequency = k * (c / (2 * math.pi)) * math.sqrt(total_hole_area / (cavity_volume * effective_length))
            return round(frequency, 2)
        else:
            raise ValueError("Paramètres nécessaires manquants ou incorrects.")
    
    except Exception as e:
        st.error(f"Erreur de calcul : {str(e)}")
        return None

# Interface utilisateur
st.title("Calculateur de Fréquence de Résonance de Helmholtz")
with st.expander("Image"):
    st.image("https://media.cheggcdn.com/media%2F352%2F352c4c43-1624-4466-b3f7-0854654c3ca1%2FphplUUdj3.png")
st.markdown("""
Cette application calcule la fréquence de résonance d'un résonateur de Helmholtz en fonction des paramètres fournis.
""")

with st.sidebar:
    st.header("Paramètres d'entrée")
    
    # Paramètres principaux
    temperature = st.number_input("Température (°C)", -50.0, 100.0, 20.0)
    thickness_mm = st.number_input("Épaisseur du matériau (mm)", 0.1, 100.0, 1.0)
    hole_diameter_mm = st.number_input("Diamètre du trou (mm)", 0.1, 50.0, 5.0)
    material_diameter_mm = st.number_input("Diamètre du matériau (mm)", 1.0, 1000.0, 100.0)
    airgap_mm = st.number_input("Espace d'air (mm)", 0.1, 100.0, 10.0)
    k = st.number_input("Coefficient de correction (k)", 0.1, 2.0, 1.0, 0.1)
    
    # Méthode de calcul des trous
    hole_method = st.radio("Méthode de calcul des trous", ["Nombre de trous", "Densité de trous"])
    
    if hole_method == "Nombre de trous":
        number_of_holes = st.number_input("Nombre de trous", 1, 1000, 10)
        density = None
    else:
        density = st.number_input("Densité de trous (/cm²)", 0.1, 100.0, 5.0)
        number_of_holes = None
    
    # Paramètre variable
    vary_param = st.selectbox("Varier un paramètre", ["Aucun", "Température", "Épaisseur", "Diamètre du trou", "Espace d'air", "Diamètre du matériau"])
    
    param_range = None
    if vary_param != "Aucun":
        st.subheader("Plage de paramètres")
        min_val = st.number_input("Valeur minimale", 0.0, 1000.0, 0.0)
        max_val = st.number_input("Valeur maximale", 0.0, 1000.0, 100.0)
        steps = st.number_input("Nombre de points", 10, 1000, 100)
        param_range = np.linspace(min_val, max_val, steps)

# Calcul principal
if st.sidebar.button("Calculer"):
    if vary_param == "Aucun":
        # Calcul simple
        if hole_method == "Densité de trous":
            material_area_cm2 = (math.pi * (material_diameter_mm / 20)**2)  # cm²
            number_of_holes = density * material_area_cm2
        
        result = calculate_frequency(
            temperature, thickness_mm, hole_diameter_mm,
            int(number_of_holes), material_diameter_mm,
            airgap_mm, k
        )
        
        if result:
            st.success(f"**Fréquence de résonance :** {result} Hz")
    
    else:
        # Calcul avec paramètre variable
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
            
            # Mise à jour du paramètre variable
            if vary_param == "Température":
                params["temperature"] = val
            elif vary_param == "Épaisseur":
                params["thickness_mm"] = val
            elif vary_param == "Diamètre du trou":
                params["hole_diameter_mm"] = val
            elif vary_param == "Espace d'air":
                params["airgap_mm"] = val
            elif vary_param == "Diamètre du matériau":
                params["material_diameter_mm"] = val
            
            # Calcul du nombre de trous si densité est utilisée
            if hole_method == "Densité de trous":
                material_area_cm2 = (math.pi * (params["material_diameter_mm"] / 20)**2)
                params["number_of_holes"] = density * material_area_cm2
            
            # Calcul de la fréquence
            freq = calculate_frequency(**params)
            frequencies.append(freq)
            parameters.append(val)
        
        # Affichage du graphique
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(parameters, frequencies, 'b-')
        ax.set_xlabel(vary_param)
        ax.set_ylabel("Fréquence (Hz)")
        ax.grid(True)
        st.pyplot(fig)
        
        # Export des données
        df = pd.DataFrame({"Paramètre": parameters, "Fréquence (Hz)": frequencies})
        st.download_button(
            label="Télécharger les données (CSV)",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name='data_frequence_resonance.csv',
            mime='text/csv'
        )

# Informations supplémentaires
with st.expander("Théorie et coefficients de correction"):
    st.markdown("""
    **Formule utilisée :**
    
    La fréquence de résonance est donnée par la formule :

    $$
    f = k \cdot \frac{c}{2 \pi} \cdot \sqrt{\frac{A}{V \cdot L_{eff}}}
    $$

    où :
    - $c$ = vitesse du son ($331 + 0.6 \cdot T^\circ$C)
    - $A$ = aire totale des trous
    - $V$ = volume de la cavité
    - $L_{eff}$ = épaisseur + correction d'extrémité ($0.85 \cdot \text{diamètre du trou}$)
    - $k$ = coefficient de correction
    """)


    st.markdown("""
    **Coefficients de correction :**
    - Ceux-ci dépendent de la géométrie exacte et des conditions aux limites
    - Valeur par défaut pour k = 1 pour une estimation théorique
    - À ajuster empiriquement pour correspondre aux mesures réelles
    """)

st.markdown("---")
st.caption("Références : [Une bouteille de thé comme résonateur de Helmholtz](https://arxiv.org/abs/2108.00444) | [Étude sur les largeurs de résonance](https://arxiv.org/abs/2203.17216)")
