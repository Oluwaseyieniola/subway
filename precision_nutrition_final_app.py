import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="Precision Nutrition Unified MVP", layout="centered")

# =====================================================================
# UTILITIES
# =====================================================================
def roundf(x, d=1): return round(float(x), d)

# ---------- wearable simulation ----------
def gen_wearable(days=7, seed=42):
    np.random.seed(seed)
    base = datetime.date.today()
    rows = []
    for i in range(days):
        rows.append({
            "date": base - datetime.timedelta(days=i),
            "steps": np.random.randint(3500, 12500),
            "strain": roundf(np.random.uniform(5, 18)),
            "HRV": np.random.randint(35, 90),
            "sleep_eff": roundf(np.random.uniform(70, 98)),
            "protein": np.random.randint(55, 160),
            "meal_timing": roundf(np.random.uniform(0.6, 1.0), 2)
        })
    return pd.DataFrame(rows)

# ---------- supply‑chain simulation ----------
def simulate_supply(food):
    np.random.seed(abs(hash(food)) % 10**6)
    stages = ["Farm", "Processing", "Cold Storage", "Transport", "Retail Shelf"]
    loss = np.random.uniform(0, 12, len(stages))
    handling = np.random.uniform(6, 10, len(stages))
    validity = 1 - loss/100 + (handling/10)*0.05
    return pd.DataFrame({
        "Stage": stages,
        "Temp°C": np.random.uniform(0,25,len(stages)).round(1),
        "Days": np.random.uniform(1,5,len(stages)).round(1),
        "Handling": handling.round(1),
        "NutrientLoss%": loss.round(1),
        "ValidityIndex": (validity*100).round(1)
    })

# ---------- large dummy food dataset ----------
def nutrient_pool():
    foods = [
        "Salmon","Sardines","Avocado","Spinach","Kale","Broccoli","Blueberries",
        "Oats","Sweet Potato","Brown Rice","Lentils","Chickpeas","Almonds",
        "Walnuts","Greek Yogurt","Eggs","Chicken Breast","Turkey Breast",
        "Lean Beef","Tofu","Tempeh","Olive Oil","Tomatoes","Garlic","Ginger"
    ]
    np.random.seed(7)
    df = pd.DataFrame({
        "Food": foods,
        "Protein": np.random.randint(3,35,len(foods)),
        "Fiber": np.random.uniform(1,12,len(foods)).round(1),
        "GI": np.random.randint(25,80,len(foods)),
        "GoodFats": np.random.uniform(0,20,len(foods)).round(1),
        "Antioxidants": np.random.randint(40,100,len(foods))
    })
    return df

# ---------- narrative metadata ----------
meta_map = {
    "Salmon": ("Omega‑3 EPA/DHA", "Reduces inflammation; supports brain & heart."),
    "Oats": ("β‑Glucan fiber", "Lowers LDL cholesterol; stabilizes glucose."),
    "Blueberries": ("Polyphenols", "Protect cells from oxidative stress."),
    "Lentils": ("Resistant starch", "Improves gut microbiome & insulin response."),
    "Avocado": ("Monounsaturated fats", "Raises HDL; balances hormones."),
    "Spinach": ("Nitrates & Iron", "Boosts oxygen delivery & energy."),
    "Garlic": ("Allicin compounds", "Enhances immunity & vascular health."),
    "Ginger": ("Gingerols", "Modulates inflammation and digestion.")
}

# =====================================================================
# APP NAVIGATION
# =====================================================================
st.title("🥗 Precision Nutrition + Supply‑Chain Unified Prototype")
page = st.sidebar.radio("Navigation",
    ["1️⃣ Profile & Wearables","2️⃣ Supply Chain Monitor","3️⃣ Detailed Recommendations"]
)

# ---------------------------------------------------------------------
# PAGE 1 – USER & WEARABLES
# ---------------------------------------------------------------------
if page.startswith("1️⃣"):
    st.header("User Profile and Wearable Snapshot")
    with st.form("profile"):
        age = st.number_input("Age",18,80,35)
        sex = st.selectbox("Sex",["F","M"])
        BMI = st.number_input("Body Mass Index",15.0,40.0,25.0)
        goal = st.selectbox("Goal",["weight_loss","energy_boost","glucose_control"])
        activity = st.selectbox("Activity Level",["low","moderate","high"])
        stress = st.selectbox("Stress Level",["low","medium","high"])
        sleep = st.number_input("Average Sleep Hours",4.0,9.0,7.0)
        submit = st.form_submit_button("Generate")
    if submit:
        w = gen_wearable()
        st.session_state["user"] = {
            "age":age,"sex":sex,"BMI":BMI,"goal":goal,
            "activity":activity,"stress":stress,"sleep":sleep,
            "HRV":int(w.HRV.mean()),"strain":float(w.strain.mean()),
            "region":"UAE"
        }
        st.dataframe(w)
        st.bar_chart(w[["steps","strain","sleep_eff"]].set_index("date"))
        st.success("User data stored – open Supply Chain Monitor next.")

# ---------------------------------------------------------------------
# PAGE 2 – SUPPLY CHAIN
# ---------------------------------------------------------------------
elif page.startswith("2️⃣"):
    st.header("Food Supply Chain Monitoring (Integrity Simulation)")
    foods = [
        "Salmon","Broccoli","Oats","Blueberries","Lentils","Tomatoes","Avocado"
    ]
    choice = st.selectbox("Select food to analyze", foods)
    df = simulate_supply(choice)
    validity = round(df.ValidityIndex.mean(),1)
    st.session_state.setdefault("validity",{})[choice] = validity
    st.dataframe(df)
    st.bar_chart(df.set_index("Stage")[["NutrientLoss%","ValidityIndex"]])
    st.metric("Overall Nutrient Integrity %", validity)
    st.success("Supply‑chain data recorded — move to Detailed Recommendations.")

# ---------------------------------------------------------------------
# PAGE 3 – RECOMMENDATIONS
# ---------------------------------------------------------------------
elif page.startswith("3️⃣"):
    user = st.session_state.get("user")
    val_map = st.session_state.get("validity",{})
    if not user:
        st.warning("Run Profile page first.")
        st.stop()

    st.header("🔬 Personalized Nutrition Insights and Food Guidance")

    df = nutrient_pool()
    df["Validity"]=[val_map.get(f,np.random.randint(75,95)) for f in df.Food]

    def score(row):
        goal=user["goal"]; s=row.Validity
        if goal=="weight_loss": s+=0.3*(30-row.GI)+0.2*row.Fiber
        elif goal=="energy_boost": s+=0.3*row.Protein+0.2*row.GoodFats
        elif goal=="glucose_control": s+=0.3*(50-row.GI)+0.3*row.Fiber
        return round(s,1)

    df["MatchScore"]=df.apply(score,axis=1)
    df=df.sort_values("MatchScore",ascending=False)

    long_term={
        "weight_loss":"helps regulate appetite, enhance fat oxidation, and maintain lean mass.",
        "energy_boost":"improves ATP production, muscular recovery, and metabolic resilience.",
        "glucose_control":"supports insulin sensitivity and prevents long‑term metabolic decline."
    }[user["goal"]]

    st.subheader(f"Foods Optimized for {user['goal'].replace('_',' ').title()}")
    for _,r in df.head(10).iterrows():
        nutrient,mech = meta_map.get(r.Food,("Key micronutrients","General metabolic support"))
        st.markdown(
            f"### 🍽️ {r.Food}\n"
            f"- **Integrity:** {r.Validity}% (supply‑chain verified)\n"
            f"- **Key Nutrient:** {nutrient}\n"
            f"- **Mechanism:** {mech}\n"
            f"- **Long‑term Benefit:** {long_term}\n"
            f"- **Nutrition Profile:** Protein {r.Protein} g  |  Fiber {r.Fiber} g  |  GI {r.GI}"
        )

    stores=pd.DataFrame({
        "Food":np.repeat(df.Food.head(10),2),
        "Store":np.tile(["Carrefour Dubai Marina","Spinneys Abu Dhabi"],20),
        "Quality":np.random.choice(["High Integrity","Standard"],20,p=[0.8,0.2]),
        "Price (AED)":np.random.randint(5,40,20)
    })
    st.subheader("🇦🇪 Store Options (High‑Integrity Sources)")
    st.dataframe(stores)

    st.success(
        f"Your plan focuses on verified, nutrient‑dense foods to optimize **{user['goal'].replace('_',' ')}**, "
        f"reduce disease risk, and build sustainable habits over time."
    )
