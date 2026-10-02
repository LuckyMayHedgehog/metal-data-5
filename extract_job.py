import os
import shutil
import json
import firebase_admin
from firebase_admin import credentials, db


FIREBASE_KEY_PATH = "metals-24324-firebase-adminsdk-fbsvc-62a521da33.json"
FIREBASE_URL = "https://metals-24324-default-rtdb.firebaseio.com/"


def init_firebase():

    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_URL
        })


def extract_metal_data_job(date: str, feature: str, raw_dir: str) -> str:

    init_firebase()

    target_folder = os.path.join(raw_dir, feature.lower(), date)

    #Забезпечення ідемпотентності
    if os.path.exists(target_folder):
        shutil.rmtree(target_folder)

    os.makedirs(target_folder, exist_ok=True)

    ref = db.reference(f'/metals_history/{date}')
    snapshot = ref.get()

    if not snapshot:
        raise ValueError(f"No data found for date: {date}")

    rates = snapshot.get('rates', {})
    matched_data = None
    target_feature = feature.lower()

    feature_aliases = {
        "gold": ["gold", "gld"],
        "silver": ["silver", "slv"],
        "platinum": ["platinum", "pt"],
        "palladium": ["palladium", "pd"],
        "rhodium": ["rhodium", "rh"],
        "iridium": ["iridium", "ir"],
        "ruthenium": ["ruthenium", "ru"]
    }

    valid_names = feature_aliases.get(target_feature, [target_feature])

    for code, details in rates.items():
            
            if isinstance(details, dict):
                name_val = details.get("name", "").lower() #name: "Gold" -> gold
                code_val = code.lower() #gld..

                if code_val in valid_names or name_val in valid_names:
                    matched_data = details
                    matched_data["ticker_code"] = code
                    break


    if matched_data is None:
        raise ValueError(f"No matching data found for feature: {feature}, {date}")


    result_payload ={
        'date': date,
        'feature': feature,
        'data': matched_data
    }


    file_path = os.path.join(target_folder, f"{date}.json")
    with open(file_path, 'w') as f:
        json.dump(result_payload, f, indent=4)


    print("Data extraction completed successfully.")

    return file_path