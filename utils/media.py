from io import BytesIO
import streamlit as st

def save_matplotlib_figure_to_bytes(fig, *, key: str, title:str, dpi: int = 200):
    """Capture a Matplotlib figure as PNG bytes and register it in session state."""
    bio = BytesIO()
    fig.savefig(bio, dpi=dpi, bbox_inches="tight", format="png")
    bio.seek(0)
    st.session_state.viz_images["items"].append({
        "key": key, "title": title, "bytes": bio.getvalue(), "mime": "image/png"
    })

def register_png_file_path(path:str, *, key: str, title: str):
    """Read a PNG from disk and register it (for pm4py outputs)."""
    with open(path, "rb") as f:
        data = f.read()
    st.session_state.viz_images["items"].append({
        "key": key, "title": title, "bytes": data, "mime": "image/png"
    })

def rl_image_from_bytes(image_bytes: bytes, max_width_pt: float):
    """
    Create a reportlab Platypus Image from raw PNG bytes and scale to max width.
    Uses Pillow to get intrinsic size; returns an Image fed by a BytesIO.
    """
    # Lazy imports to avoid hard deps at module import time
    from PIL import Image as PILImage
    from reportlab.platypus import Image as RLImage

    # Open with Pillow to read size
    bio_in = BytesIO(image_bytes)
    with PILImage.open(bio_in) as pil_img:
        iw, ih = pil_img.size
        # Scale to fit max width, but don't upscale
        scale = min(max_width_pt / float(iw), 1.0)
        out_w, out_h = iw * scale, ih * scale

        # Re-encode to PNG bytes for a fresh clean stream
        bio_out = BytesIO()
        pil_img.save(bio_out, format="PNG")
        bio_out.seek(0)

    # Pass file-like object to ReportLab Image
    return RLImage(bio_out, width=out_w, height=out_h)