import os
from flask import Flask, request, jsonify
from extract_job import extract_metal_data_job

app = Flask(__name__)
#браузер  ->Post-> Flask server ->check data-> extract.. ->GetsData-> saves ->Flask: response

DEFAULT_RAW_DIR = os.path.join(os.getcwd(), "storage", "raw")


@app.route("/extract", methods=["POST"])
#if someone sends a POST request to /extract, this function will be called

def handle_extract():

    # 1. Перевіряємо, чи надійшов JSON
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Content-Type повинен бути application/json"
        }), 400

    payload = request.get_json()

    # 2. Зчитуємо обов'язкові параметри з тіла запиту
    date = payload.get("date")
    feature = payload.get("feature")
    
    raw_dir = payload.get("raw_dir", DEFAULT_RAW_DIR)

    if not date or not feature:
        return jsonify({
            "status": "error",
            "message": "Поля 'date' та 'feature' є обов'язковими для виконання завдання"
        }), 400

    # 3. Викликаємо джобу збереження даних
    try:
        saved_file_path = extract_metal_data_job(
            date=str(date),
            feature=str(feature),
            raw_dir=raw_dir
        )
        
        return jsonify({
            "status": "success",
            "message": f"Data for feature '{feature}' on date '{date}' has been extracted and saved successfully.",
            "file_path": saved_file_path
        }), 200

    except ValueError as ve:
        return jsonify({
            "status": "not_found",
            "message": str(ve)
        }), 404

    except Exception as e:
        return jsonify({
            "status": "internal_error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    print("Запуск Flask сервера на http://127.0.0.1:8081 ...")
    app.run(host="127.0.0.1", port=8081, debug=True)

