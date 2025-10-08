pip install scikit-learn numpy bibtexparser
pip install spacy
python -m spacy download en_core_web_sm

# Primero, actualiza pip
python.exe -m pip install --upgrade pip

# Segundo, instala el conjunto de librerías compatibles
pip install numpy==1.26.4 "spacy==3.7.2" scikit-learn scipy

# Tercero, asegura el modelo de lenguaje
python -m spacy download en_core_web_sm

