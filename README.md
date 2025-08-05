# Mapa de Códigos Postales (España)

Aplicación web hecha con Python y Streamlit para visualizar sobre un mapa los códigos postales introducidos.

## Funcionalidades

- Introducir lista de códigos postales
- Visualizar su localización en un mapa interactivo
- Descargar el mapa en HTML
- Ver tabla de códigos mapeados, localidad y número de repeticiones
- Descargar tabla como HTML

## Requisitos

- Python 3.9 o superior
- pip
- Librerías en `requirements.txt`

## Cómo ejecutar

```bash
cd mapa_codigos_postales
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py