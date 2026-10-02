import os
import shutil
import json
import unittest
from unittest.mock import patch 
#підміняє відповідь Firebase заздалегідь підготовленими тестовими даними

# Імпортуємо функцію джоби
from extract_job import extract_metal_data_job


class TestExtractJob(unittest.TestCase):

    def setUp(self):
        #Виконується перед кожним окремим тестом    
        # Створюємо ізольовану тимчасову папку для тестів
        self.test_raw_dir = os.path.join(os.getcwd(), "tests_temp_storage", "raw")
        self.test_date = "2024-09-03"
        self.test_feature = "gold"

    def tearDown(self):
        #Виконується після кожного окремого тесту 
        temp_dir = os.path.join(os.getcwd(), "tests_temp_storage")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    @patch("extract_job.init_firebase") #які файли підміняємо, щоб не робити реальний запит до Firebase
    @patch("extract_job.db.reference")
    def test_job_creates_correct_file_and_content(self, mock_db_ref, mock_init):
        #Перевірка коректності шляху створення файлу та його вмісту
        # знімок даних, який повернув Firebase
        mock_snapshot = {
            "rates": {
                "GLD": {
                    "name": "Gold",
                    "category": "metal",
                    "value": 230.29,
                    "source": "Yahoo Finance"
                }
            }
        }
        mock_db_ref.return_value.get.return_value = mock_snapshot

        # Запускаємо джобу
        result_path = extract_metal_data_job(
            date=self.test_date,
            feature=self.test_feature,
            raw_dir=self.test_raw_dir
        )

        # Очікувані шляхи 
        expected_dir = os.path.join(self.test_raw_dir, "gold", self.test_date)
        expected_file = os.path.join(expected_dir, f"{self.test_date}.json")

        # Перевірки )
        self.assertEqual(result_path, expected_file)
        self.assertTrue(os.path.exists(expected_file), "Файл не було створено на диску!")

        # Перевіряємо вміст записаного JSON
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["feature"], "gold")
            self.assertEqual(data["date"], self.test_date)
            self.assertEqual(data["data"]["value"], 230.29)

    @patch("extract_job.init_firebase")
    @patch("extract_job.db.reference")
    def test_job_idempotency_cleans_old_files(self, mock_db_ref, mock_init):
        #Перевірка ідемпотентності — видалення старих файлів у директорії
        mock_snapshot = {
            "rates": {
                "GLD": {"name": "Gold", "value": 230.29}
            }
        }
        mock_db_ref.return_value.get.return_value = mock_snapshot

        target_dir = os.path.join(self.test_raw_dir, "gold", self.test_date)
        os.makedirs(target_dir, exist_ok=True)
        
        # Створюємо фіктивний застарілий файл, який має бути видалений джобою
        old_file = os.path.join(target_dir, "old_garbage_data.json")
        with open(old_file, "w", encoding="utf-8") as f:
            f.write('{"old": "data"}')

        self.assertTrue(os.path.exists(old_file), "Старий файл обов'язково має існувати перед запуском")

        # Викликаємо джобу
        extract_metal_data_job(
            date=self.test_date,
            feature=self.test_feature,
            raw_dir=self.test_raw_dir
        )

        # cтарого файлу більше немає, а новий існує
        self.assertFalse(os.path.exists(old_file), "Старий файл не був видалений! Джоба не очистила папку.")
        self.assertTrue(os.path.exists(os.path.join(target_dir, f"{self.test_date}.json")))

    @patch("extract_job.init_firebase")
    @patch("extract_job.db.reference")
    def test_job_raises_value_error_if_metal_not_found(self, mock_db_ref, mock_init):
        #Перевірка викидання ValueError, якщо вказаний метал відсутній
        # База повернула лише індекс, металу немає
        mock_snapshot = {
            "rates": {
                "^GSPC": {"name": "S&P 500", "value": 5500.0}
            }
        }
        mock_db_ref.return_value.get.return_value = mock_snapshot

        with self.assertRaises(ValueError):
            extract_metal_data_job(
                date=self.test_date,
                feature="non_existing_metal",
                raw_dir=self.test_raw_dir
            )


if __name__ == "__main__":
    unittest.main()