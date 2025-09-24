# PARA_vc.py
# - 자바 미사용: kiwipiepy로 명사 추출
# - SBERT 유사도 점수로 관련 용어 상위 3~5개 선정
# - 토큰 경계 기준으로 첫 1회만 빈칸 처리(부분문자열 훼손 방지)
# - 출력: 상위 용어 + 유사도, 퀴즈 텍스트, 정답 확인

from typing import List, Tuple
from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer, util
from math_list import get_terms

# ===== 설정 =====
MODEL_NAME = 'snunlp/KR-SBERT-V40K-klueNLI-augSTS'
MIN_BLANKS = 3
MAX_BLANKS = 5
STOPWORDS = {"수학", "정리"}  # 필요시 추가

# ===== 전역 객체 =====
kiwi = Kiwi()
sentence_model = SentenceTransformer(MODEL_NAME)

def get_user_input() -> Tuple[str, str]:
    topic = input("주제를 입력하세요: ")
    text = input("관련된 글을 입력하세요: ")
    return topic, text

def extract_noun_tokens(text: str):
    """전체 토큰을 돌려주되, N* 품사만 명사 후보로 취급."""
    return kiwi.tokenize(text)

def nouns_in_text(tokens, vocab: set) -> List[str]:
    """문장 내 명사 토큰 중 vocab(수학용어 사전)에 있는 것만 순서대로, 중복 제거."""
    seen = set()
    result = []
    for tk in tokens:
        if tk.tag.startswith("NN"):
            w = tk.form
            if w in vocab and w not in STOPWORDS and w not in seen:
                seen.add(w)
                result.append(w)
    return result

def rank_terms_by_similarity(topic: str, terms: List[str]) -> List[Tuple[str, float]]:
    """SBERT로 topic과 term 문장 유사도 계산 후 내림차순 정렬."""
    if not terms:
        return []
    cleaned_topic = topic.replace(" ", "")
    topic_sentence = cleaned_topic + "와 관련된 수학 개념"
    term_sentences = [t + "라는 수학 용어" for t in terms]

    topic_vec = sentence_model.encode(topic_sentence, convert_to_tensor=True)
    term_vecs = sentence_model.encode(term_sentences, convert_to_tensor=True)
    sims = util.pytorch_cos_sim(topic_vec, term_vecs)[0]  # shape: [len(terms)]

    # 내림차순 인덱스
    sorted_idx = sims.argsort(descending=True)
    ranked = [(terms[int(i)], float(sims[int(i)])) for i in sorted_idx]
    return ranked

def choose_k(ranked_terms: List[Tuple[str, float]], min_k=MIN_BLANKS, max_k=MAX_BLANKS):
    """3~5개 범위에서 가능한 만큼 선택."""
    n = len(ranked_terms)
    k = min(max_k, max(min_k, n))
    return ranked_terms[:k]

def build_spans_for_masking(text: str, tokens, target_terms: List[str]):
    """토큰 경계 기반 첫 1회 등장 위치(span)만 수집."""
    spans = []  # (start, end, term)
    remaining = set(target_terms)
    for tk in tokens:
        if tk.form in remaining:
            spans.append((tk.start, tk.start + tk.len, tk.form))
            remaining.remove(tk.form)
        if not remaining:
            break
    # 등장 순으로 정렬
    spans.sort(key=lambda x: x[0])
    ordered_terms = [t for _, _, t in spans]
    return spans, ordered_terms

def mask_spans(text: str, spans: List[Tuple[int, int, str]]) -> str:
    """뒤에서부터 안전하게 치환해서 인덱스 무너지지 않게 처리."""
    if not spans:
        return text
    chars = list(text)
    for s, e, _ in reversed(spans):
        chars[s:e] = list("____")
    return "".join(chars)

def main():
    # 1) 데이터 준비
    math_terms = set(get_terms("math_terms.txt"))  # 파일에서 수학 용어 로드
    topic, text = get_user_input()

    # 2) 문장 내 명사 후보 추출 (사전과 교집합)
    tokens = extract_noun_tokens(text)
    candidate_terms = nouns_in_text(tokens, math_terms)

    if not candidate_terms:
        print("\n주제와 관련된 용어가 없음.")
        return

    # 3) SBERT 유사도 순으로 정렬
    ranked = rank_terms_by_similarity(topic, candidate_terms)
    if not ranked:
        print("\n주제와 관련된 용어가 없음.")
        return

    # 4) 상위 3~5개 선택 (가능 수량 내)
    top_terms_with_scores = choose_k(ranked, MIN_BLANKS, MAX_BLANKS)
    top_terms = [t for t, _ in top_terms_with_scores]

    # 5) 실제 텍스트에 등장하는 첫 토큰만 빈칸 처리(span 계산)
    spans, ordered_terms_in_text = build_spans_for_masking(text, tokens, top_terms)

    if not spans:
        print("\n선정된 용어가 텍스트에 실제로 나타나지 않았습니다.")
        return

    # 6) 출력: 유사도 / 퀴즈 / 정답확인
    print("\n주제와 관련된 상위 용어들(유사도):")
    for i, (term, score) in enumerate(top_terms_with_scores, 1):
        mark = " (본문 미등장)" if term not in ordered_terms_in_text else ""
        print(f"{i}. {term} (유사도: {score:.3f}){mark}")

    quiz_text = mask_spans(text, spans)
    print("\n퀴즈 형식:")
    print(quiz_text)

    user_answer = input("\n빈칸에 들어갈 단어들을 순서대로 입력하세요 (띄어쓰기로 구분함): ").split()

    print("\n정답 확인:")
    for i, (correct, user) in enumerate(zip(ordered_terms_in_text, user_answer), 1):
        print(f"{i}. {user} {'✅ 정답' if correct == user else f'❌ (정답: {correct})'}")

if __name__ == "__main__":
    main()
