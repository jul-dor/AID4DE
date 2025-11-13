from io import BytesIO
import streamlit as st
import matplotlib.pyplot as plt
import textwrap
import pandas as pd

def _ensure_viz_store():
    st.session_state.setdefault("viz_images", {"items": []})

def _upsert_viz_item(new_item: dict):
    """Replace existing item with same 'key' or append if not present."""
    _ensure_viz_store()
    items = st.session_state["viz_images"]["items"]
    for i, it in enumerate(items):
        if it.get("key") == new_item.get("key"):
            items[i] = new_item
            break
    else:
        items.append(new_item)

def register_png_file_path(path: str, *, key: str, title: str, type_hint: str | None = None):
    """Read a bitmap (e.g., PNG) from disk and register it for export."""
    with open(path, "rb") as f:
        data = f.read()
    _upsert_viz_item({
        "key": key, "title": title, "bytes": data,
        "mime": "image/png", "type": type_hint or "image"
    })

def register_matplotlib_figure(fig, *, key: str, title: str, dpi: int = 150, type_hint: str | None = None):
    """Save a Matplotlib figure as PNG bytes and register for PDF export."""
    bio = BytesIO()
    fig.savefig(bio, format="png", dpi=dpi, bbox_inches="tight")
    bio.seek(0)
    _upsert_viz_item({
        "key": key, "title": title, "bytes": bio.getvalue(),
        "mime": "image/png", "type": type_hint or "image"
    })

def register_dataframe_as_image(df, *, key: str, title: str, max_rows: int = 40, dpi: int = 150):
    """Render a pandas DataFrame as a Matplotlib table image and register it, with wrapped text for long cells."""

    if not isinstance(df, pd.DataFrame):
        if isinstance(df, dict):
            df = pd.DataFrame(list(df.items()), columns=["Key", "Value"])
        elif isinstance(df, pd.Series):
            df = df.to_frame().reset_index()
            df.columns = ["Key", "Value"]
        else:
            df = pd.DataFrame(df)

    df_to_plot = df.head(max_rows).copy()

    def _wrap_cell(x, width=25):
        if isinstance(x, str):
            return "\n".join(textwrap.wrap(x, width=width))
        return x

    wrapped_df = df_to_plot.applymap(_wrap_cell)

    fig_w = min(12, max(8, len(wrapped_df.columns) * 2))
    fig_h = min(12,  max(3, (len(wrapped_df) + 1) * 0.6))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    tbl = ax.table(cellText=wrapped_df.values, colLabels=wrapped_df.columns, loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(7)
    tbl.scale(1, 1.5)

    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold")
        cell.set_edgecolor("#666666")

    plt.title(title, fontsize=10, pad=8)

    from io import BytesIO
    bio = BytesIO()
    fig.savefig(bio, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    bio.seek(0)

    _upsert_viz_item({
        "key": key,
        "title": title,
        "bytes": bio.getvalue(),
        "mime": "image/png",
        "type": "table"
    })


def rl_image_from_bytes(image_bytes: bytes, max_width_pt: float):
    from PIL import Image as PILImage
    from reportlab.platypus import Image as RLImage

    bio_in = BytesIO(image_bytes)
    with PILImage.open(bio_in) as pil_img:
        iw, ih = pil_img.size
        scale = min(max_width_pt / float(iw), 1.0)
        out_w, out_h = iw * scale, ih * scale
        bio_out = BytesIO()
        pil_img.save(bio_out, format="PNG")
        bio_out.seek(0)

    return RLImage(bio_out, width=out_w, height=out_h)

def register_kv_table_for_export(
    rows, *, key: str, title: str,
    col_widths_cm=(6.0, 10.0)
):
    """
    Register a key/value table for the PDF export using ReportLab (not an image).
    `rows` should be a list of (key, value) tuples or a 2-col DataFrame.
    Text will auto-wrap and row height adjusts automatically.
    """
    # Normalize input
    try:
        import pandas as pd
        if hasattr(rows, "to_dict"):
            rows = list(pd.DataFrame(rows).values.tolist())
    except Exception:
        pass

    item = {
        "key": key,
        "title": title,
        "type": "rl_table",       
        "rows": rows,             
        "col_widths_cm": list(col_widths_cm),
        "mime": "application/x-rl-table",
    }

    _upsert_viz_item(item)