import streamlit as st
import pandas as pd
import time

# ---------------------------------------------------------
# 1. 초기 설정 및 데이터 로드
# ---------------------------------------------------------
st.set_page_config(page_title="아빠표 단어 시험", page_icon="📝")

# 세션 상태 초기화
if 'quiz_state' not in st.session_state:
    st.session_state['quiz_state'] = 'SETUP' 
if 'current_index' not in st.session_state:
    st.session_state['current_index'] = 0
if 'score' not in st.session_state:
    st.session_state['score'] = 0
if 'wrong_answers' not in st.session_state:
    st.session_state['wrong_answers'] = []
if 'quiz_data' not in st.session_state:
    st.session_state['quiz_data'] = []
# 이전 문제의 결과 피드백을 저장할 변수 (즉시 다음 문제로 넘어가기 때문)
if 'last_feedback' not in st.session_state:
    st.session_state['last_feedback'] = None # (메시지, 정답여부Boolean)

# 데이터 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('vocab.csv')
        df['English'] = df['English'].str.strip()
        df['Korean'] = df['Korean'].str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame()

df = load_data()

# ---------------------------------------------------------
# 2. 기능 함수 (엔터키 쳤을 때 실행될 로직)
# ---------------------------------------------------------
def check_answer():
    # 현재 문제 정보 가져오기
    current_idx = st.session_state['current_index']
    data = st.session_state['quiz_data']
    
    # 퀴즈가 끝난 상태면 아무것도 안 함
    if current_idx >= len(data):
        return

    current_word = data[current_idx]
    user_input = st.session_state.user_input # 입력값 가져오기
    correct_answer = current_word['English']

    # 정답 비교 logic
    if user_input.strip().lower() == correct_answer.strip().lower():
        st.session_state['score'] += 1
        # 피드백 저장 (메시지, True)
        st.session_state['last_feedback'] = (f"⭕ 정답! '{correct_answer}'", True)
    else:
        # 오답 저장
        st.session_state['wrong_answers'].append({
            'English': correct_answer,
            'Korean': current_word['Korean'],
            'My Answer': user_input
        })
        # 피드백 저장 (메시지, False)
        st.session_state['last_feedback'] = (f"❌ 땡! 정답은 '{correct_answer}' (입력: {user_input})", False)

    # 다음 문제로 인덱스 증가
    st.session_state['current_index'] += 1
    
    # 입력창 비우기
    st.session_state.user_input = ""

# ---------------------------------------------------------
# 3. 화면 구성
# ---------------------------------------------------------
st.title("⚡ Speed 단어 시험")

# (A) 설정 화면
if st.session_state['quiz_state'] == 'SETUP':
    if not df.empty:
        st.info("엔터키를 치면 바로 채점하고 다음 문제로 넘어갑니다!")
        days = df['Day'].unique()
        selected_day = st.selectbox("Day 선택", days)
        
        if st.button("시험 시작하기!"):
            day_data = df[df['Day'] == selected_day]
            st.session_state['quiz_data'] = day_data.sample(frac=1).reset_index(drop=True).to_dict('records')
            st.session_state['quiz_state'] = 'TESTING'
            st.session_state['current_index'] = 0
            st.session_state['score'] = 0
            st.session_state['wrong_answers'] = []
            st.session_state['last_feedback'] = None
            st.rerun()
    else:
        st.error("'vocab.csv' 파일을 넣어주세요.")

# (B) 시험 화면
elif st.session_state['quiz_state'] == 'TESTING':
    total_q = len(st.session_state['quiz_data'])
    current_idx = st.session_state['current_index']

    # 1. 종료 조건 확인
    if current_idx >= total_q:
        st.session_state['quiz_state'] = 'FINISHED'
        st.rerun()

    current_word = st.session_state['quiz_data'][current_idx]
    
    # 2. 진행률 바
    st.progress(current_idx / total_q)
    
    # 3. [중요] 이전 문제 결과 피드백 영역 (화면 상단 고정)
    # 다음 문제로 바로 넘어가므로, 지난 문제 결과를 여기서 보여줍니다.
    if st.session_state['last_feedback']:
        msg, is_correct = st.session_state['last_feedback']
        if is_correct:
            st.success(msg)
        else:
            st.error(msg)
    else:
        st.write("시작해볼까요? 화이팅!")

    st.markdown("---")

    # 4. 문제 제시
    st.markdown(f"#### 문제 {current_idx + 1}/{total_q}")
    st.markdown(f"## 뜻: <span style='color:blue'>{current_word['Korean']}</span>", unsafe_allow_html=True)

    # 5. 입력창 (버튼 없음, 엔터치면 check_answer 실행)
    st.text_input(
        label="영어 단어를 입력하고 Enter를 치세요",
        key="user_input",        # 이 key를 통해 값을 읽고 씁니다
        on_change=check_answer   # 엔터 키 감지 시 실행할 함수
    )
    
    # 포커스는 Streamlit 특성상 on_change 후 다시 렌더링될 때 자동으로 이 입력창에 유지됩니다.

# (C) 결과 화면
elif st.session_state['quiz_state'] == 'FINISHED':
    score = st.session_state['score']
    total = len(st.session_state['quiz_data'])
    
    st.balloons()
    st.header(f"끝! 점수: {score} / {total}")
    
    # 마지막 문제에 대한 피드백도 보여주기 위해
    if st.session_state['last_feedback']:
        msg, is_correct = st.session_state['last_feedback']
        if is_correct:
            st.success(f"마지막 문제: {msg}")
        else:
            st.error(f"마지막 문제: {msg}")

    if st.session_state['wrong_answers']:
        st.markdown("### 🚨 틀린 단어 (스크린샷 찍어두세요!)")
        st.table(pd.DataFrame(st.session_state['wrong_answers']))
    
    if st.button("처음으로"):
        st.session_state['quiz_state'] = 'SETUP'
        st.session_state['last_feedback'] = None
        st.rerun()