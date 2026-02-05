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
    st.image(img, caption=selected_image, use_container_width=True)
    st.subheader("Verification Settings")
    user_count = st.number_input("Enter expected number of samples:", min_value=0, step=1)

    if st.button("Analyse"):
        with st.spinner("Analysing image..."):
            prompt = (
                "The image shows a laboratory rack containing blood samples. "
                "Please count how many blood samples are there in the rack."
                "First count the available slots in the rack. It is always AxB, a rectangle."
                "also provide a matrix representation of the rack where 1 represents a vial and 0 represents an empty slot. Format the matrix as rows of numbers separated by spaces."
                "Only return one sentence for the count: This rack contains X vials. followed by the matrix on new lines."
            )
            result = analyse_image_with_llm(img_path, prompt)

            # Extract number from LLM response
            match = re.search(r'This rack contains (\d+) vials', result, re.IGNORECASE)
            if not match:
                 match = re.search(r'\d+', result)

            if match:
                llm_count = int(match.group(1)) if len(match.groups()) > 0 else int(match.group())
                
                st.markdown("---")
                st.subheader("Verification Result")
                
                if user_count > 0:
                    if user_count == llm_count:
                        st.success(f"✅ Correct! The count matches the expected value ({llm_count}).")
                    else:
                        st.error(f"❌ Mismatch! LLM found {llm_count}, but you expected {user_count}.")
                else:
                    st.warning("Please enter an expected count > 0 above to verify the result.")
                
                # Extract and display Matrix
                st.subheader("Rack Layout")
                # Look for lines that look like matrix rows (only 0s and 1s and spaces)
                lines = result.split('\n')
                matrix_lines = []
                for line in lines:
                    stripped = line.strip()
                    # Check if line contains only 0, 1, and spaces
                    if stripped and all(c in '01 []' for c in stripped) and len(stripped) > 2:
                        matrix_lines.append(stripped)
                
                if matrix_lines:
                    # Create HTML for the grid
                    html = "<div style='display: flex; flex-direction: column; gap: 5px;'>"
                    for row in matrix_lines:
                        html += "<div style='display: flex; gap: 5px;'>"
                        for char in row.split():
                            if char == '1':
                                color = '#4CAF50' # Green
                                text = '1'
                            elif char == '0':
                                color = '#f0f0f0' # Light Gray
                                text = '0'
                            else:
                                continue # Skip spaces or other chars
                            
                            html += f"<div style='width: 30px; height: 30px; background-color: {color}; display: flex; align-items: center; justify-content: center; border-radius: 4px; font-weight: bold; color: {'white' if char == '1' else 'black'};'>{text}</div>"
                        html += "</div>"
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.info("No matrix representation found in response.")

