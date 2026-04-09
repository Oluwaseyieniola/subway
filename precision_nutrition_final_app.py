import streamlit as st
import pandas as pd
import numpy as np
import datetime

# =====================================================================
#  SETUP & GENERIC UTILS
# =====================================================================
st.set_page_config(page_title="Precision Nutrition Unified MVP", layout="centered")

def roundf(x, digits=1):  # safe rounding helper
    return round(float(x), digits)

# ---------- Synthetic wearable data ----------
def generate_wearable(days=7, seed=42):
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

# ---------- Supply-chain simulation ----------
def simulate_supply(food):
    np.random.seed(abs(hash(food)) % 10**6)
    stages = ["Farm", "Processing", "Cold Storage", "Transport", "Retail Shelf"]
    loss = np.random.uniform(0, 12, len(stages))
    handling = np.random.uniform(6, 10, len(stages))
    validity = 1 - loss/100 + (handling/10)*0.05
    return pd.DataFrame({"Stage": stages,
                         "Temp°C": np.random.uniform(0,25,len(stages)).round(1),
                         "Duration(d)": np.random.uniform(1,5,len(stages)).round(1),
                         "Handling": handling.round(1),
                         "NutrientLoss(%)": loss.round(1),
                         "ValidityIndex": (validity*100).round(1)})

# ---------- Global synthetic nutrient data ----------
def food_nutrients():
    foods = ["Broccoli","Chicken","Oats","Blueberries","Tomatoes","Eggs","Lentils"]
    np.random.seed(9)
    return pd.DataFrame({
        "Food": foods,
        "Protein": np.random.randint(3,30,len(foods)),
        "Fiber": np.random.uniform(1,10,len(foods)).round(1),
        "GI": np.random.randint(30,80,len(foods)),
        "Antioxidants": np.random.randint(40,100,len(foods))
    })

# =====================================================================
#  STREAMLIT WORKFLOW
# =====================================================================

st.title("🥗 Precision Nutrition + Supply‑Chain Unified Prototype")

page = st.sidebar.radio("Navigate",
    ["1️⃣ Profile & Wearables", "2️⃣ Supply Chain Monitor", "3️⃣ Personalized Recommendations"]
)

# ---------------------------------------------------------------------
# PAGE 1 — USER & WEARABLE INPUT
# ---------------------------------------------------------------------
if page.startswith("1️⃣"):
    st.header("User Health Profile and Synthetic Wearable Data")
    with st.form("user_form"):
        age = st.number_input("Age",18,80,35)
        sex = st.selectbox("Sex",["F","M"])
        BMI = st.number_input("Body Mass Index",15.0,40.0,25.0)
        goal = st.selectbox("Goal",["weight_loss","energy_boost","glucose_control"])
        activity = st.selectbox("Activity Level",["low","moderate","high"])
        stress = st.selectbox("Stress Level",["low","medium","high"])
        sleep = st.number_input("Average Sleep Hours",4.0,9.0,7.0)
        submit = st.form_submit_button("Generate")
    if submit:
        wear = generate_wearable()
        st.session_state["user_data"] = {
            "age":age,"sex":sex,"BMI":BMI,"goal":goal,
            "activity":activity,"stress":stress,"sleep":sleep,
            "HRV":int(wear.HRV.mean()),"strain":float(wear.strain.mean()),
            "region":"UAE"
        }
        st.dataframe(wear)
        st.bar_chart(wear[["steps","strain","sleep_eff"]].set_index("date"))
        st.success("✔ User and wearable data stored. Proceed to Supply Chain.")

# ---------------------------------------------------------------------
# PAGE 2 — SUPPLY‑CHAIN MONITOR
# ---------------------------------------------------------------------
elif page.startswith("2️⃣"):
    st.header("Food Supply‑Chain Tracking & Integrity Simulation")
    foods = ["Broccoli","Chicken","Oats","Blueberries","Tomatoes","Eggs","Lentils"]
    choice = st.selectbox("Pick a food to analyze", foods)
    df = simulate_supply(choice)
    validity = df["ValidityIndex"].mean().round(1)
    st.session_state.setdefault("validity",{})[choice] = validity
    st.dataframe(df)
    st.bar_chart(df.set_index("Stage")[["NutrientLoss(%)","ValidityIndex"]])
    st.metric("Current Estimated Nutrient Integrity (%)", validity)
    st.success("✔ Supply‑chain data recorded. Move to Recommendations.")

# ---------------------------------------------------------------------
# PAGE 3 — INTEGRATED RECOMMENDER
# ---------------------------------------------------------------------
elif page.startswith("3️⃣"):
    st.header("Integrated Precision Nutrition Recommender and Store Lookup")
    
    user = st.session_state.get("user_data")
    val_map = st.session_state.get("validity",{})
    if not user:
        st.warning("Please complete Profile page first.")
    else:
        foods = food_nutrients()
        foods["Validity"] = [val_map.get(f, np.random.randint(75,95)) for f in foods["Food"]]
        # scoring
        def score(row):
            g=user["goal"]; s=row.Validity
            if g=="weight_loss": s+=0.3*(30-row.GI)+0.2*row.Fiber
            elif g=="energy_boost": s+=0.3*row.Protein+0.1*row.GI
            elif g=="glucose_control": s+=0.4*(50-row.GI)+0.2*row.Fiber
            return round(s,1)
        foods["MatchScore"]=foods.apply(score,axis=1)
        foods=foods.sort_values("MatchScore",ascending=False)
        st.subheader(f"Top Foods for Goal → **{user['goal'].replace('_',' ').title()}**")
        st.dataframe(foods)
        best=foods.iloc[0].Food
        st.success(f"🏆 Best match: {best} ({foods.iloc[0].Validity}% integrity).")
        # mock UAE stores
        stores=pd.DataFrame({
            "Food":np.repeat(foods.Food,2),
            "Store":np.tile(["Carrefour Dubai Marina","Lulu Hypermarket Abu Dhabi"],len(foods)),
            "Quality":np.random.choice(["High Integrity","Standard"],len(foods)*2,p=[0.7,0.3]),
            "Price (AED)":np.random.randint(3,25,len(foods)*2)
        })
        st.subheader("🇦🇪 UAE Stores Carrying Your Top Foods")
        st.dataframe(stores[stores["Food"].isin(foods.Food.head(3))])
        why={
            "weight_loss":"Low‑GI and fiber‑rich foods help fat loss while maintaining micronutrients.",
            "energy_boost":"Protein‑dense high‑integrity foods improve recovery and energy.",
            "glucose_control":"Verified low‑GI foods support steady blood sugar and gut health."
        }
        st.markdown("**Why these foods:** "+why.get(user["goal"],""))
