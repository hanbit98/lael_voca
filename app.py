import streamlit as st
import pandas as pd
import random # 순서 섞기용

# ---------------------------------------------------------
# 1. 초기 설정 및 데이터 로드
# ---------------------------------------------------------
st.set_page_config(page_title="아빠표 단어 시험", page_icon="📝", layout="centered")

# --- UI 커스텀 CSS (폰트 크기 조절) ---
st.markdown("""
    <style>
    /* 1. 텍스트 입력창 안의 글자 크기 및 높이 키우기 */
    div[data-baseweb="input"] input {
        font-size: 28px !important;
        font-weight: bold !important;
        padding: 15px !important;
    }
    
    /* 2. 정답/오답 피드백 알림창(success, error 등)의 글자 크기 키우기 */
    div[data-testid="stNotification"] div[data-testid="stMarkdownContainer"] p {
        font-size: 24px !important;
        font-weight: bold !important;
        line-height: 1.4 !important;
    }
    
    /* 3. 예문 폰트 크기 키우기 */
    .exam-sentence {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
        white-space: pre-wrap;  /* 👈 이 줄을 추가하세요! (연속된 공백을 그대로 유지해줍니다) */
    }
    
    /* 4. 해석 폰트 크기 키우기 및 색상 지정 */
    .korean-translation {
        font-size: 18px;
        color: #0066cc;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)


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
        # utf-8-sig로 읽어서 한글 깨짐 및 눈에 보이지 않는 특수문자(\ufeff) 문제 방지
        df = pd.read_csv('vocab.csv', encoding='utf-8-sig')
        
        # 맨 윗줄(1행)이 'Day'가 아니라 데이터('Day 01' 등)라면 헤더가 없는 것으로 간주
        if 'Day' not in df.columns:
            # 헤더 없이 다시 읽고, 이름을 강제로 지정
            df = pd.read_csv('vocab.csv', header=None, names=['Day', '순서', '정답 단어', '예문', '한글 해석'], encoding='utf-8-sig')
        else:
            # 헤더가 있는 경우, 기둥 이름을 강제로 통일 ('정답'이라고 썼을 수도 있으므로)
            df.columns = ['Day', '순서', '정답 단어', '예문', '한글 해석']
            
        # 정답 입력 시 띄어쓰기 오류 방지를 위해 공백 제거
        df['정답 단어'] = df['정답 단어'].astype(str).str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
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
    correct_answer = str(current_word['정답 단어'])

    # 정답 체크 (대소문자 무시, 공백 무시)
    if user_input.strip().lower() == correct_answer.strip().lower():
        st.session_state['score'] += 1
        st.session_state['last_feedback'] = (f"⭕ 정답! '{correct_answer}'", True)
    else:
        st.session_state['wrong_answers'].append({
            '정답 단어': correct_answer,
            '나의 답': user_input,
            '예문': current_word.get('예문', ''),
            '한글 해석': current_word.get('한글 해석', '')
        })
        st.session_state['last_feedback'] = (f"❌ 땡! 정답은 '{correct_answer}' (입력: {user_input})", False)

    st.session_state['current_index'] += 1
    st.session_state.user_input = ""

# ---------------------------------------------------------
# 3. 화면 구성
# ---------------------------------------------------------
# 타이틀
st.markdown("<h2 style='font-size: 30px;'>❤️보석같은 라엘❤️ 단어시험 뽀개기😁</h2>", unsafe_allow_html=True)

# (A) 설정 화면
if st.session_state['quiz_state'] == 'SETUP':
    if not df.empty:
        st.info("엔터키를 치면 바로 채점하고 다음 문제로 넘어갑니다!")
        if 'Day' in df.columns:
            days = df['Day'].unique()
            selected_day = st.selectbox("Day 선택", days)
        else:
            st.error("CSV 파일 구조에 문제가 있습니다. 파일 형식을 확인해주세요.")
            st.stop()
        
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
        st.error("'vocab.csv' 파일을 넣어주세요. (단어1부터 바로 시작해도 됩니다!)")

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

    # 예문과 한글 해석 출력 (빈칸을 자동으로 넓게 치환)
    exam_text = current_word.get('예문', '').replace('( )', '( &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; )').replace('()', '( &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; )')
    st.markdown(f"<div class='exam-sentence'>{exam_text}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='korean-translation'>{current_word.get('한글 해석', '')}</div>", unsafe_allow_html=True)

    st.text_input(
        label="빈칸에 들어갈 영어 단어를 입력하고 Enter를 치세요",
        key="user_input",
        on_change=check_answer
    )

# (C) 결과 화면
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
        
        # 틀린 문제 표 출력
        wrong_df = pd.DataFrame(st.session_state['wrong_answers'])
        wrong_df.index = wrong_df.index + 1 # 0,1,2...를 1,2,3...으로 변경
        st.table(wrong_df)
        
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
                
                # 상태 리셋
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