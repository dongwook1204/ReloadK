document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('quiz-form');
    const quizContainer = document.getElementById('quiz-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const messageArea = document.getElementById('message-area');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        quizContainer.innerHTML = '';
        quizContainer.classList.add('hidden');
        messageArea.classList.add('hidden');
        loadingSpinner.classList.remove('hidden');

        const topic = document.getElementById('topic').value;
        const text = document.getElementById('text').value;

        try {
            const response = await fetch('/generate_quiz', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic, text }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                displayGeneratedContent(data.payload);
            } else {
                showMessage(data.message, 'error');
            }
        } catch (error) {
            console.error('Fetch Error:', error);
            showMessage('네트워크 연결 또는 서버 상태를 확인해 주세요.', 'error');
        } finally {
            loadingSpinner.classList.add('hidden');
        }
    });

    // LLM이 생성한 콘텐츠를 표시하는 함수
    function displayGeneratedContent(data) {
        quizContainer.innerHTML = '';
        quizContainer.classList.remove('hidden');

        // 줄바꿈 문자(\n)를 HTML <br> 태그로 변환하여 표시
        const resultHTML = `
            <div class="concept-section">
                <h3>📖 핵심 개념 설명</h3>
                <div class="quiz-text-area">${data.concept_explanation.replace(/\n/g, '<br>')}</div>
            </div>
            
            <div class="problem-section">
                <h3>❓ 응용 문제</h3>
                <div class="quiz-text-area">${data.application_problem.replace(/\n/g, '<br>')}</div>
            </div>
            
            <form id="answer-check-form" style="margin-top: 1.5rem;">
                <div class="form-group">
                    <label for="user-answer">응용 문제 정답 입력</label>
                    <input type="text" id="user-answer" placeholder="정답을 입력하고 확인 버튼을 누르세요" required>
                </div>
                <button type="submit" class="check-answer-btn">정답 확인</button>
            </form>

            <div id="check-result" class="card hidden" style="margin-top: 1rem; padding: 1.5rem;">
                </div>
        `;

        quizContainer.innerHTML = resultHTML;

        // 정답 확인 이벤트 리스너 추가
        document.getElementById('answer-check-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const userAnswer = document.getElementById('user-answer').value.trim();
            checkAndDisplayAnswer(userAnswer, data.answer, data.solution);
        });
    }
    
    // 정답을 확인하고 결과를 표시하는 함수
    function checkAndDisplayAnswer(userAnswer, correctAnswer, solution) {
        const resultDiv = document.getElementById('check-result');
        const isCorrect = normalizeAnswer(userAnswer) === normalizeAnswer(correctAnswer);
        
        let resultHTML = '';
        let resultIcon = '';
        let resultMessage = '';
        let resultClass = '';
        
        // 정답 여부에 따른 메시지와 스타일 설정
        if (isCorrect) {
            resultIcon = '✅';
            resultMessage = '정답입니다! 잘하셨어요!';
            resultClass = 'success';
        } else {
            resultIcon = '❌';
            resultMessage = '아쉽지만 오답입니다. 해설을 참고하여 다시 풀어보세요.';
            resultClass = 'error';
        }

        // 결과 및 해설 HTML 생성
        resultHTML = `
            <div class="answer-feedback ${resultClass}">
                <span style="font-size: 1.5rem; margin-right: 10px;">${resultIcon}</span>
                <span style="font-weight: 600;">${resultMessage}</span>
            </div>
            
            <h4 style="margin-top: 1rem;">정답</h4>
            <p style="font-weight: 600; color: var(--text-color);">${correctAnswer.replace(/\n/g, '<br>')}</p>
            
            <h4>🔍 해설</h4>
            <p>${solution.replace(/\n/g, '<br>')}</p>
        `;

        resultDiv.innerHTML = resultHTML;
        resultDiv.classList.remove('hidden');
    }

    // 답안을 비교하기 전에 불필요한 공백, 대소문자 등을 통일하는 함수
    function normalizeAnswer(answer) {
        // 모든 공백 제거하고, 소문자로 변환하여 비교의 정확도를 높입니다.
        // LLM이 생성하는 답에 따라 정규화 기준을 추가할 수 있습니다.
        return answer.replace(/\s/g, '').toLowerCase();
    }

    function showMessage(msg, type) {
        messageArea.textContent = msg;
        messageArea.classList.remove('hidden', 'error', 'success', 'warning');
        messageArea.classList.add(type);
    }
});