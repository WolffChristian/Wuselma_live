import streamlit as st

def apply_custom_css():
    st.markdown("""
        <style>
        /* 1. GRUNDGERÜST */
        [data-testid="stSidebar"] { display: none; }
        .stApp { background-color: #001220 !important; }
        
        /* 2. TEXT & ÜBERSCHRIFTEN */
        h1, h2, h3, p, span, label { color: #ffffff !important; }

        /* 3. BUTTONS (Basis von dir + 3D Schatten) */
        div.stButton > button, 
        button[kind="primaryFormSubmit"], 
        button[kind="secondaryFormSubmit"] {
            background-color: #004a99 !important;
            color: white !important;
            border-radius: 10px !important;
            font-weight: 800 !important;
            width: 100% !important;
            
            /* NUR DIESE DREI ZEILEN SIND NEU FÜR 3D */
            border: none !important;
            border-bottom: 4px solid #002d5e !important;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.3) !important;
        }

        /* 4. DATEI-UPLOAD */
        [data-testid="stFileUploader"] section {
            background-color: #001f3f !important;
            border: 2px dashed #004a99 !important;
            color: white !important;
        }
        [data-testid="stFileUploader"] section button {
            background-color: #ff8c00 !important;
            color: white !important;
            border: none !important;
        }

        /* 5. HOVER-EFFEKTE (Standard von dir) */
        div.stButton > button:hover {
            background-color: #ff8c00 !important;
            color: white !important;
            border-bottom: 4px solid #b36200 !important;
        }

        /* 6. EINGABEFELDER & TABS */
        .stTextInput input, .stNumberInput input, .stTextArea textarea, 
        div[data-baseweb="select"] > div {
            background-color: #001f3f !important;
            color: white !important;
            border: 2px solid #004a99 !important;
        }
        .stTabs [aria-selected="true"] { background-color: #ff8c00 !important; }

        /* 7. EXPANDER */
        div[data-testid="stExpander"] {
            background-color: #001f3f !important;
            border: 1px solid #004a99 !important;
            border-radius: 8px !important;
            margin-bottom: 1rem !important;
        }
        div[data-testid="stExpander"] summary {
            background-color: #001f3f !important;
            color: white !important;
        }

        /* 8. BILD-VERGRÖSSERN BUTTON */
        div[data-testid="stImage"] button,
        button[data-testid="stImageFullScreenBtn"] {
            background-color: #004a99 !important;
            color: white !important;
            border: 2px solid #ffffff !important;
            border-radius: 8px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def show_header():
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2:
        try:
            st.image("assets/Kopf_seite.png", use_container_width=True)
        except:
            st.title("WuselMap")
    st.divider()