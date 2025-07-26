import os
import joblib
import numpy as np
from django.shortcuts import render
from collections import Counter

# Load all components from the bundled .pkl file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'dis_model.pkl')
model_bundle = joblib.load(MODEL_PATH)

model = model_bundle['model']
vectorizer = model_bundle['vectorizer']
label_encoder = model_bundle['label_encoder']
symptom_rule_map = model_bundle['symptom_rule_map']
disease_weights = model_bundle['disease_weights']

def home(request):
    all_symptoms = vectorizer.get_feature_names_out()
    return render(request, 'home.html', {'symptoms': sorted(all_symptoms)})

def predict(request):
    all_symptoms = vectorizer.get_feature_names_out()

    if request.method == 'POST':
        selected_symptoms = request.POST.getlist('symptoms')
        selected_symptoms = [s.strip().lower().replace(" ", "_") for s in selected_symptoms]

        if not selected_symptoms:
            return render(request, 'form.html', {
                'symptoms': all_symptoms,
                'error': "Please select at least one symptom.",
                'scroll_to': "predict"
            })

        if len(selected_symptoms) <= 2:

            matched_diseases = []
            for symptom in selected_symptoms:
                matched_diseases.extend(symptom_rule_map.get(symptom, []))

            if matched_diseases:
                disease_counter = Counter(matched_diseases)
                top_disease = disease_counter.most_common(1)[0][0]
            else:
                top_disease = "Unknown"

            return render(request, 'form.html', {
                'predicted_disease': top_disease,
                'precautions': ["Drink water", "Rest well", "Consult a doctor"],
                'symptoms': vectorizer.get_feature_names_out(),
                'scroll_to': "predict"
            })
        
        # ML-based prediction
        input_text = ' '.join(selected_symptoms)
        input_vector = vectorizer.transform([input_text])
        probs = model.predict_proba(input_vector)[0]

        top_indices = np.argsort(probs)[-3:][::-1]
        top_diseases = [(label_encoder.inverse_transform([i])[0], round(probs[i]*100, 2)) for i in top_indices]

        return render(request, 'form.html', {
            'predicted_disease': top_diseases[0][0],
            'top_diseases': top_diseases,
            'precautions': ["Stay hydrated", "Take rest", "Consult a doctor if symptoms persist"],
            'symptoms': all_symptoms,
            'scroll_to': "predict"
        })

    return render(request, 'form.html', {'symptoms': all_symptoms})
