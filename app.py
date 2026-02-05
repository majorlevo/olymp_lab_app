import streamlit as st
import os
from PIL import Image
import re
from llm_api import analyse_image_with_llm

st.set_page_config(page_title="Olymp Kokshetau Lab - Blood Sample Rack Check")
st.title("Olymp Kokshetau Laboratory - Blood Sample Rack Check")

IMAGES_DIR = "images"

st.sidebar.header("Image Upload")
uploaded_file = st.sidebar.file_uploader("Select a rack image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image_path = os.path.join(IMAGES_DIR, uploaded_file.name)
    with open(image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"Image uploaded: {uploaded_file.name}")

st.header("Available Images")
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

image_files = [f for f in os.listdir(IMAGES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

selected_image = st.selectbox("Select image for analysis", image_files)

if selected_image:
    img_path = os.path.join(IMAGES_DIR, selected_image)
    img = Image.open(img_path)
    st.image(img, caption=selected_image, use_column_width=True)
    if st.button("Analyse"):
        with st.spinner("Analysing image..."):
            prompt = (
                "The image shows a laboratory rack containing blood samples. "
                "Please count how many blood samples are there in the rack."
                "First count the available slots in the rack. It is always AxB, a rectangle."
                "Only return one sentence: This rack contains X vials."
            )
            result = analyse_image_with_llm(img_path, prompt)
        st.subheader("Analysis result:")
        # Result processing if list format
        if result and ":" in result:
            lines = result.split("\n") if "\n" in result else [result]
            for line in lines:
                items = [x.strip() for x in line.split(",") if ":" in x]
                for item in items:
                    slot, status = item.split(":", 1)
                    status = status.strip().lower()
                    if "empty" in status:
                        st.markdown(f"<span style='color:gray'>Slot {slot}: <b>Empty</b></span>", unsafe_allow_html=True)
                    elif "blood" in status:
                        st.markdown(f"<span style='color:red'>Slot {slot}: <b>Blood sample</b></span>", unsafe_allow_html=True)
                    else:
                        st.write(f"Slot {slot}: {status}")
        else:
            st.write(result)
            
            # Extract number from LLM response
            match = re.search(r'\d+', result)
            if match:
                llm_count = int(match.group())
                
                st.markdown("---")
                st.subheader("Verification")
                user_count = st.number_input("Enter actual number of samples:", min_value=0, step=1)
                
                if user_count > 0:
                    if user_count == llm_count:
                        st.success(f"✅ Correct! The count matches the LLM result ({llm_count}).")
                    else:
                        st.error(f"❌ Mismatch! LLM found {llm_count}, but you counted {user_count}.")

