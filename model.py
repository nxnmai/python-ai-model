import json
import pandas as pd

class CareerQuizModel:
    """
    Lớp xử lý logic của quiz, giờ đây có khả năng đọc câu hỏi từ file CSV.
    """

    def __init__(self, config_path, questions_csv_path):
        """Hàm khởi tạo, nhận vào đường dẫn của 2 file cấu hình."""
        self.config_path = config_path
        self.questions_csv_path = questions_csv_path
        self.questions = []
        self.career_profiles = {}
        self._load_data()

    def _parse_scores(self, score_string):
        """
        Hàm phụ để chuyển một chuỗi điểm "key1:val1;key2:val2" thành dictionary.
        Ví dụ: "frontend_dev:3;pm_ba_po:1" -> {"frontend_dev": 3, "pm_ba_po": 1}
        """
        scores = {}
        if not isinstance(score_string, str):
            return scores
        
        try:
            pairs = score_string.split(';')
            for pair in pairs:
                if ':' in pair:
                    key, value = pair.split(':')
                    scores[key.strip()] = int(value.strip())
        except ValueError:
            print(f"Cảnh báo: Định dạng điểm bị lỗi và không thể đọc: '{score_string}'")
        return scores

    def _load_questions_from_csv(self):
        """Hàm mới: Đọc và chuyển đổi dữ liệu từ file CSV."""
        try:
            df = pd.read_csv(self.questions_csv_path)
            
            required_cols = ['id', 'prompt', 'option_A_text', 'option_A_scores', 
                             'option_B_text', 'option_B_scores']
            if not all(col in df.columns for col in required_cols):
                print("Lỗi: File CSV thiếu các cột cần thiết (id, prompt, option_A_text, option_A_scores, ...).")
                return

            temp_questions = []
            for _, row in df.iterrows():
                question = {
                    "id": row['id'],
                    "prompt": row['prompt'],
                    "options": {
                        "A": {
                            "text": row['option_A_text'],
                            "scores": self._parse_scores(row['option_A_scores'])
                        },
                        "B": {
                            "text": row['option_B_text'],
                            "scores": self._parse_scores(row['option_B_scores'])
                        }
                    }
                }
                if 'option_C_text' in df.columns and pd.notna(row['option_C_text']):
                    question['options']['C'] = {
                        "text": row['option_C_text'],
                        "scores": self._parse_scores(row.get('option_C_scores', ''))
                    }
                if 'option_D_text' in df.columns and pd.notna(row['option_D_text']):
                    question['options']['D'] = {
                        "text": row['option_D_text'],
                        "scores": self._parse_scores(row.get('option_D_scores', ''))
                    }
                temp_questions.append(question)
            self.questions = temp_questions
        except FileNotFoundError:
            print(f"Lỗi: Không tìm thấy file câu hỏi CSV tại '{self.questions_csv_path}'.")
        except Exception as e:
            print(f"Lỗi không xác định khi đọc file CSV: {e}")

    def _load_data(self):
        """Hàm tải dữ liệu tổng hợp: gọi hàm đọc JSON và CSV."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.career_profiles = config_data.get('career_profiles', {})
        except FileNotFoundError:
            print(f"Lỗi nghiêm trọng: Không tìm thấy file config tại '{self.config_path}'.")
            return
        
        self._load_questions_from_csv()

        if not self.questions or not self.career_profiles:
            print("Cảnh báo: Dữ liệu câu hỏi hoặc ngành nghề chưa được tải thành công.")

    def calculate_scores(self, user_answers):
        """Hàm logic chính (mapping), không thay đổi."""
        scores = {career_key: 0 for career_key in self.career_profiles.keys()}
        for question_id, answer_key in user_answers.items():
            for question in self.questions:
                if question['id'] == question_id:
                    option = question['options'].get(answer_key)
                    if option and 'scores' in option:
                        for career, points in option['scores'].items():
                            if career in scores:
                                scores[career] += points
                    break
        return scores

    def get_recommendations(self, scores, top_n=3):
        """Hàm trả về gợi ý, không thay đổi."""
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        recommendations = []
        for career_key, score in sorted_scores[:top_n]:
            recommendations.append({
                "career_name": self.career_profiles.get(career_key, "Không rõ"),
                "score": score
            })
        return recommendations

if __name__ == "__main__":
    print("--- CHẠY MÔ PHỎNG MODEL VỚI DỮ LIỆU TỪ CSV ---")
    
    # Tạo file config.json giả lập để code chạy được
    config_content = {
      "career_profiles": {
        "software_eng": "Software Engineer", "qa_qc_eng": "QA/QC Engineer",
        "backend_dev": "Backend Developer", "frontend_dev": "Frontend Developer",
        "tester": "Tester", "pm_ba_po": "Project Manager/BA/PO",
        "cloud_devops": "Cloud/DevOps Engineer", "solutions_architect": "Solutions Architect",
        "ai_ml_eng": "AI/ML Engineer", "data_science": "Data Science/Analysis/Engineer"
      }
    }
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config_content, f)

    model = CareerQuizModel(config_path='config.json', questions_csv_path='Questions.csv')

    if model.questions and model.career_profiles:
        print("\nTải dữ liệu thành công!")
        
        # Lấy ID câu hỏi có sẵn từ dữ liệu đã tải để mô phỏng
        available_question_ids = [q['id'] for q in model.questions]
        mock_user_answers = {}
        if len(available_question_ids) >= 3:
             mock_user_answers = {
                available_question_ids[0]: "A",
                available_question_ids[1]: "C",
                available_question_ids[2]: "B", 
            }

        print(f"\nGiả lập input của người dùng: {mock_user_answers}")

        final_scores = model.calculate_scores(mock_user_answers)
        print(f"\nBảng điểm đã được tính toán: {final_scores}")

        top_3_recommendations = model.get_recommendations(final_scores, top_n=3)
        
        print("\n--- KẾT QUẢ GỢI Ý HÀNG ĐẦU ---")
        for i, rec in enumerate(top_3_recommendations):
            print(f"{i+1}. {rec['career_name']} (Điểm: {rec['score']})")
    else:
        print("\nKhông thể chạy mô phỏng do lỗi tải dữ liệu.")