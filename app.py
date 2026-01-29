import streamlit as st
import pandas as pd
import random # 순서 섞기용

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
if 'last_feedback' not in st.session_state:
    st.session_state['last_feedback'] = None

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
# 2. 기능 함수
# ---------------------------------------------------------
def check_answer():
    current_idx = st.session_state['current_index']
    data = st.session_state['quiz_data']
    
    if current_idx >= len(data):
        return

    current_word = data[current_idx]
    user_input = st.session_state.user_input
    correct_answer = current_word['English']

    if user_input.strip().lower() == correct_answer.strip().lower():
        st.session_state['score'] += 1
        st.session_state['last_feedback'] = (f"⭕ 정답! '{correct_answer}'", True)
    else:
        st.session_state['wrong_answers'].append({
            'English': correct_answer,
            'Korean': current_word['Korean'],
            'My Answer': user_input
        })
        st.session_state['last_feedback'] = (f"❌ 땡! 정답은 '{correct_answer}' (입력: {user_input})", False)

    st.session_state['current_index'] += 1
    st.session_state.user_input = ""

# ---------------------------------------------------------
# 3. 화면 구성
# ---------------------------------------------------------
# 기존 st.title("⚡ Speed 단어 시험") 부분을 아래로 교체하세요
st.title("⚡라엘이❤️의 DYB 단어시험 뽀개기😁")

# (A) 설정 화면
if st.session_state['quiz_state'] == 'SETUP':
    if not df.empty:
        st.info("엔터키를 치면 바로 채점하고 다음 문제로 넘어갑니다!")
        days = df['Day'].unique()
        selected_day = st.selectbox("Day 선택", days)
        
        if st.button("시험 시작하기!"):
            day_data = df[df['Day'] == selected_day]
            # 전체 데이터 셔플
            st.session_state['quiz_data'] = day_data.sample(frac=1).reset_index(drop=True).to_dict('records')
            
            # 상태 초기화
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

    if current_idx >= total_q:
        st.session_state['quiz_state'] = 'FINISHED'
        st.rerun()

    current_word = st.session_state['quiz_data'][current_idx]
    
    st.progress(current_idx / total_q)
    
    # 상단 피드백 영역
    if st.session_state['last_feedback']:
        msg, is_correct = st.session_state['last_feedback']
        if is_correct:
            st.success(msg)
        else:
            st.error(msg)
    else:
        st.write("시작해볼까요? 화이팅!")

    st.markdown("---")
    st.markdown(f"#### 문제 {current_idx + 1}/{total_q}")
    st.markdown(f"## 뜻: <span style='color:blue'>{current_word['Korean']}</span>", unsafe_allow_html=True)

    st.text_input(
        label="영어 단어를 입력하고 Enter를 치세요",
        key="user_input",
        on_change=check_answer
    )

# (C) 결과 화면 (여기가 수정되었습니다)
elif st.session_state['quiz_state'] == 'FINISHED':
    score = st.session_state['score']
    total = len(st.session_state['quiz_data'])
    
    st.balloons()
    st.header(f"끝! 점수: {score} / {total}")

    # 마지막 문제 피드백
    if st.session_state['last_feedback']:
        msg, is_correct = st.session_state['last_feedback']
        if is_correct:
            st.success(f"마지막 문제: {msg}")
        else:
            st.error(f"마지막 문제: {msg}")

    # 틀린 문제가 있을 경우
    if st.session_state['wrong_answers']:
        st.markdown("### 🚨 틀린 단어 확인하기")
        
        # [수정된 부분 시작] -----------------------
        wrong_df = pd.DataFrame(st.session_state['wrong_answers'])
        wrong_df.index = wrong_df.index + 1 # 0,1,2...를 1,2,3...으로 변경
        st.table(wrong_df)
        # [수정된 부분 끝] -------------------------
        
        st.warning("👇 틀린 문제만 모아서 다시 시험 볼 수 있어요!")
        
        # 버튼 두 개를 나란히 배치
        col1, col2 = st.columns(2)
        
        with col1:
            # [재시험 버튼]
            if st.button("🔥 틀린 문제만 다시 풀기"):
                # 틀린 문제 데이터를 가져와서 새로운 퀴즈 데이터로 설정
                retry_data = st.session_state['wrong_answers'].copy()
                random.shuffle(retry_data) # 순서 섞기
                
                st.session_state['quiz_data'] = retry_data
                
                # 상태 리셋 (중요: wrong_answers를 비워야 재시험 오답을 새로 담음)
                st.session_state['quiz_state'] = 'TESTING'
                st.session_state['current_index'] = 0
                st.session_state['score'] = 0
                st.session_state['wrong_answers'] = [] 
                st.session_state['last_feedback'] = None
                st.rerun()
        
        with col2:
            # [처음으로 버튼]
            if st.button("🏠 처음으로 돌아가기"):
                st.session_state['quiz_state'] = 'SETUP'
                st.session_state['last_feedback'] = None
                st.rerun()
                
    else:
        # 다 맞았을 경우
        st.success("완벽합니다! 틀린 문제가 하나도 없네요! 🎉")
        if st.button("🏠 처음으로 돌아가기"):
            st.session_state['quiz_state'] = 'SETUP'
            st.session_state['last_feedback'] = None
            st.rerun()