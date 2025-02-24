# Helmholtz Resonator Frequency Calculator

This interactive Python application calculates the resonance frequency of a Helmholtz resonator based on user-defined parameters. Built with **Streamlit**, it provides a user-friendly interface to explore the physics of Helmholtz resonators.

---

## Features

- **Interactive Inputs**: Users can input parameters such as temperature, material thickness, hole diameter, number of holes, and more.
- **Dynamic Calculations**: The app computes the resonance frequency using the Helmholtz resonator formula.
- **Parameter Variation**: Users can vary one parameter at a time and visualize its effect on the resonance frequency using a graph.
- **Data Export**: Results can be exported as a CSV file for further analysis.
- **Theoretical Insights**: Detailed explanations and formulas are provided within the app.

---

## How to Use

1. **Access the App**: Visit the deployed app on [Streamlit Community Cloud](helmholtz.streamlit.app).
2. **Run Calculations**:
   - Click the "Calculate" button to compute the resonance frequency.
   - If a parameter range is selected, a graph will display showing the frequency variation.
3. **Export Data**:
   - Use the "Download Data" buttons to export the results as CSV, PDF or JPEG file.

---

## Installation (Local Development)

To run this app locally, follow these steps:

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/LinoVation1312/helmotz.git
   cd helmotz
Install Dependencies:

   ```bash
pip install -r requirements.txt
Run the App:
```
 ```bash
streamlit run helmotz_freq.py
```
Access the App:

Open your browser and go to (https://helmotz.streamlit.app/).

Parameters
The app uses the following parameters to calculate the resonance frequency:

Temperature (°C): Ambient temperature affecting the speed of sound.
Material Thickness (mm): Thickness of the resonator material.
Hole Diameter (mm): Diameter of the holes in the resonator.
Number of Holes: Total number of holes (or hole density).
Material Diameter (mm): Diameter of the resonator material.
Airgap (mm): Distance between the resonator and the backing surface.
Correction Factor (k): Empirical correction factor for the formula.
Formula
The resonance frequency 


Deployment
This app is deployed using Streamlit Community Cloud. Any changes pushed to the main branch of the GitHub repository will automatically update the deployed app.

References
A bottle of tea as a Helmholtz resonator
Resonance widths for Helmholtz resonators
Contributing
Contributions are welcome! If you'd like to improve this project, please:

Fork the repository.
Create a new branch for your feature or bug fix.
Submit a pull request.
License
This project is licensed under the MIT License. See the LICENSE file for details.

Author

Lino CONORD
Email: lino.conord@gmail.com






