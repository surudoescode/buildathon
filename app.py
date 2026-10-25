import streamlit as st
import json
import os
from reconstruction import PhoenixReconstructor
from engine.renderer import BlueprintRenderer
from inference import resurrect_from_image

# Optional storage integration if available
try:
    from storage import get_evidence_records
except ImportError:
    get_evidence_records = None

st.set_page_config(page_title="Phoenix | Software Resurrection", layout="wide")

st.title("Project Phoenix: Autonomous Software Resurrection")
st.caption("Reconstructing legacy systems from visual and runtime evidence with verifiable parity.")

# Sidebar controls
st.sidebar.header("Execution Controls")
selected_version = st.sidebar.selectbox("Active Candidate Version", ["v1", "v2"], index=0)

reconstructor = PhoenixReconstructor()
rule_cfg = reconstructor.rule_manager.get_rule_config(selected_version)
st.sidebar.info(f"**Candidate {selected_version.upper()} Rule:**\n{rule_cfg.get('description')}")

tabs = st.tabs(["🎮 Reconstructed App", "📷 Vision Resurrection", "🧪 5-Scenario Parity Verification", "💻 Export Code"])

# Tab 1: Live Interactive Reconstructed App
with tabs[0]:
    st.subheader(reconstructor.blueprint.get("title", "Reconstructed Invoice Terminal"))
    
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None

    form_values = {}
    action_triggered = False

    for comp in reconstructor.blueprint.get("components", []):
        if comp["type"] == "button":
            if BlueprintRenderer.render_component(comp, {}):
                action_triggered = True
        elif comp["type"] == "display_metrics":
            BlueprintRenderer.render_component(comp, {"last_result": st.session_state["last_result"]})
        else:
            val = BlueprintRenderer.render_component(comp, form_values)
            form_values[comp["id"]] = val

    if action_triggered:
        try:
            res = reconstructor.execute(form_values, version=selected_version)
            st.session_state["last_result"] = res
            st.rerun()
        except Exception as e:
            st.error(f"Execution Error: {e}")

# Tab 2: Vision Ingestion
with tabs[1]:
    st.subheader("Multimodal Extraction (Vision Resurrection)")
    st.write("Upload a legacy screenshot to infer UI elements and application blueprints.")
    
    uploaded_file = st.file_uploader("Upload Legacy Screen Image", type=["png", "jpg", "jpeg"])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Uploaded Legacy Interface", width=400)
        if st.button("Resurrect Blueprint from Image", type="primary"):
            with st.spinner("Analyzing interface and extracting rules..."):
                blueprint = resurrect_from_image(
                    image_bytes=uploaded_file.getvalue(),
                    mime_type=uploaded_file.type
                )
                st.success("Reconstruction Completed!")
                st.json(blueprint.model_dump())

# Tab 3: Parity Verification
with tabs[2]:
    st.subheader("Deterministic Parity Verification (5 Mandatory Scenarios)")
    st.write("Verifying candidate clone against legacy reference across core boundary probes.")

    if st.button("Run Verification Suite Now"):
        from test_runner import TEST_SCENARIOS, evaluate_candidate
        
        v1_res = evaluate_candidate("v1")
        v2_res = evaluate_candidate("v2")

        c1, c2 = st.columns(2)
        c1.metric("Candidate V1 Parity", f"{v1_res['score']:.0f}%")
        c2.metric("Candidate V2 (Repaired) Parity", f"{v2_res['score']:.0f}%", delta=f"+{v2_res['score'] - v1_res['score']:.0f}%")

        table_rows = []
        for r1, r2 in zip(v1_res["results"], v2_res["results"]):
            table_rows.append({
                "Scenario ID": r1["id"],
                "Condition": r1["name"],
                "Expected Total": f"₹{r1['expected']:,.2f}",
                "V1 Output": f"₹{r1['actual']:,.2f}",
                "V2 Output": f"₹{r2['actual']:,.2f}",
                "Final Parity": "🟢 PASS" if r2["passed"] else "🔴 FAIL"
            })
        st.table(table_rows)

# Tab 4: Generated Code Export
with tabs[3]:
    st.subheader("Standalone Reconstructed Source Code")
    st.write("Phoenix synthesizes clean, framework-independent modern Python code.")
    
    generated_code = reconstructor.export_application(version=selected_version)
    st.code(generated_code, language="python")
    
    st.download_button(
        label=f"Download Candidate {selected_version.upper()} (.py)",
        data=generated_code,
        file_name=f"resurrected_app_{selected_version}.py",
        mime="text/x-python"
    )
