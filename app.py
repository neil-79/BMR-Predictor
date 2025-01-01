from flask import Flask, request, render_template, jsonify, redirect, url_for, session
import joblib
import numpy as np

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session handling

# Load the Saved Model
model = joblib.load('best_bodyfat_model.pkl')

# Default Values for Less Contributing Features (mean/neutral values)
DEFAULT_VALUES = {
    'Neck': 37.5,
    'Hip': 99.0,
    'Knee': 39.0,
    'Ankle': 22.5,
    'Biceps': 30.0,
    'Forearm': 28.0,
    'Wrist': 17.0
}

@app.route('/')
def home():
    return render_template('index.html', weeks_list=[], weights_list=[])

@app.route('/guide')
def guide():
    form_data = session.get('form_data', {})
    return render_template('soma_visual_guess.html', form_data=form_data)

@app.route('/somameasurement')
def somameasurement():
    return render_template('soma_measurement.html', link_to_index=url_for('somameasurement'))

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extract Input Data for Key Features
        age = float(request.form['Age'])
        weight = float(request.form['Weight'])
        height = float(request.form['Height'])
        abdomen = float(request.form['Abdomen'])
        thigh = float(request.form['Thigh'])
        chest = float(request.form['Chest'])

        # Combine Key Features with Default Values for Other Features
        input_features = [
            age, weight, height,
            DEFAULT_VALUES['Neck'], chest, abdomen,
            DEFAULT_VALUES['Hip'], thigh, DEFAULT_VALUES['Knee'],
            DEFAULT_VALUES['Ankle'], DEFAULT_VALUES['Biceps'],
            DEFAULT_VALUES['Forearm'], DEFAULT_VALUES['Wrist']
        ]

        # Make Prediction
        input_data = np.array(input_features).reshape(1, -1)
        prediction = model.predict(input_data)[0]

        # Generate Weight Loss Data
        current_weight = weight
        weight_loss_per_week = 0.5  # Default 0.5 kg/week
        target_weight = weight - ((prediction-8) / 100 * weight)
        weeks = int((current_weight - target_weight) / weight_loss_per_week)

        weeks_list = list(range(weeks + 1))
        weights_list = [current_weight - (i * weight_loss_per_week) for i in range(weeks + 1)]

        # Return Data to Frontend
        return render_template(
            'index.html',
            prediction_text=f'Predicted Body Fat Percentage: {prediction:.2f}%',
            weeks_list=weeks_list,
            weights_list=weights_list
        )

    except Exception as e:
        return f"Error: {str(e)}"

# New Route for Main Page
@app.route('/main')
def main():
    return render_template('main.html', link_to_index=url_for('home'))

# New Functions to Calculate BMR, LBM, TDEE, Macros, and Calories to Burn
def calculate_bmr(sex, weight, height, age):
    if sex == "Male":
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def calculate_lbm(weight, body_fat):
    return weight * (1 - body_fat / 100)

def adjust_tdee(bmr, body_type):
    if body_type == "Endomorphic":
        return bmr * 1.15
    elif body_type == "Ectomorphic":
        return bmr * 1.5
    else:
        return bmr * 1.3

def calculate_macros(tdee, lbm):
    protein = lbm * 2  # 2g per kg of lean body mass
    fat = 0.25 * tdee / 9  # 25% of TDEE goes to fats (9 kcal per gram)
    carbs = (tdee - (protein * 4 + fat * 9)) / 4  # Remaining calories to carbs
    return protein, carbs, fat

def calories_to_burn(tdee):
    return 500  # Standard 500 kcal deficit for weight loss

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        # Get form data
        weight = float(request.form.get('Weight', 70))
        height = float(request.form.get('Height', 160))
        age = float(request.form.get('Age', 30))
        sex = request.form.get('Sex', 'Male')  # Default to Male if not provided
        body_fat = float(request.form.get('BodyFat', 20))  # Default to 0 if not provided
        body_type = request.form.get('BodyType', 'Endomorphic')  # Default to Endomorphic if not provided

        # Calculate Lean Body Mass (LBM)
        lbm = calculate_lbm(weight, body_fat)

        # Calculate BMR
        bmr = calculate_bmr(sex, weight, height, age)

        # Adjust TDEE based on body type
        tdee = adjust_tdee(bmr, body_type)

        # Calculate macros (Protein, Carbs, Fats)
        protein, carbs, fat = calculate_macros(tdee, lbm)

        # Calories to burn for weight loss (500 kcal deficit)
        burn_calories = calories_to_burn(tdee)

        # Check if any variable is None and provide a default
        bmr = bmr if bmr is not None else 0
        tdee = tdee if tdee is not None else 0
        lbm = lbm if lbm is not None else 0
        protein = protein if protein is not None else 0
        carbs = carbs if carbs is not None else 0
        fat = fat if fat is not None else 0

        # Store data in session for soma_visual_guess.html
        session['form_data'] = {
            'weight': weight,
            'height': height,
            'age': age,
            'sex': sex,
            'body_fat': body_fat,
            'body_type': body_type,
            'bmr': round(bmr, 2),
            'tdee': round(tdee, 2),
            'lbm': round(lbm, 2),
            'protein': round(protein, 2),
            'carbs': round(carbs, 2),
            'fat': round(fat, 2),
            'burn_calories': burn_calories
        }

        # Return results to the template
        return render_template(
            'main.html',
            bmr=round(bmr, 2),
            tdee=round(tdee, 2),
            lbm=round(lbm, 2),
            burn_calories=burn_calories,
            protein=round(protein, 2),
            carbs=round(carbs, 2),
            fat=round(fat, 2),
            weight=weight,
            height=height,
            age=age,
            sex=sex,
            body_fat=round(body_fat, 2),
            body_type=body_type
        )


    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True)


