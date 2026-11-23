import re
from io import BytesIO
from pathlib import Path

import pytesseract
import streamlit as st
from PIL import Image, ImageOps


TESSERACT_PATH = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")

if TESSERACT_PATH.is_file():
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)


@st.cache_data(show_spinner=False)
def extract_text(image_bytes):
    with Image.open(BytesIO(image_bytes)) as image:
        grayscale = ImageOps.grayscale(image)
        clean_image = ImageOps.autocontrast(grayscale)
        return pytesseract.image_to_string(clean_image, lang="eng").strip()


def words(text):
    return set(re.findall(r"\w+", text.casefold()))


st.set_page_config(page_title="Screenshot Finder", page_icon="🔎")
st.title("🔎 Screenshot Finder")
st.write("Upload screenshots and search for words written inside them.")

uploads = st.file_uploader(
    "Upload screenshots",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)

if not uploads:
    st.info("Upload a few screenshots to start.")
    st.stop()

query = st.text_input("Search screenshots", placeholder="Example: exam timetable")
query_words = words(query)

if not query_words:
    st.caption("Enter one or more words from the screenshot you want to find.")
    st.stop()

matches = []
skipped = []

with st.spinner("Reading screenshot text..."):
    for upload in uploads:
        image_bytes = upload.getvalue()

        try:
            screenshot_text = extract_text(image_bytes)
        except pytesseract.TesseractNotFoundError:
            st.error("Tesseract OCR was not found. Check the installation path.")
            st.stop()
        except pytesseract.TesseractError as error:
            st.error(f"OCR could not run. Check the Tesseract setup.\n\n{error}")
            st.stop()
        except OSError:
            skipped.append(upload.name)
            continue

        if query_words.issubset(words(screenshot_text)):
            matches.append((upload.name, image_bytes, screenshot_text))

if skipped:
    st.warning("Could not read: " + ", ".join(skipped))

if not matches:
    st.info("No match found. Try one clear word visible in the screenshot.")

st.write(f"**{len(matches)} matching screenshot(s)**")

for filename, image_bytes, screenshot_text in matches:
    st.image(image_bytes, caption=filename)
    with st.expander("Show detected text"):
        st.text(screenshot_text)