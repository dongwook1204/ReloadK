# math_list.py
def get_terms(file_path="math_terms.txt"):
    terms = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                clean_term = line.strip()
                if clean_term:
                    terms.append(clean_term)
    except FileNotFoundError:
        print(f"파일 '{file_path}'를 찾을 수 없습니다. 먼저 crawler.py를 실행해 주세요.")
    return terms

# 피타고라스 정리란 직각 삼각형의 빗변을 변으로 하는 정사각형의 넓이는 두 직각변을 각각 한 변으로 하는 정사각형 넓이의 합과 같다는 정리이다.