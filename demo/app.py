import gradio as gr
from pipeline import run_consistency_check


def run_check(input_text1, input_text2, threshold):
    """Run consistency check and return HTML badge snippet with inline styles."""
    result = run_consistency_check(input_text1, input_text2, threshold)

    # Return self-contained inline CSS styles for each badge type
    if result == "ALLOW":
        return '<div style="background-color: #064e3b; color: #34d399; border: 1px solid #059669; padding: 6px 18px; border-radius: 20px; font-weight: 700; display: inline-block; font-size: 14px; letter-spacing: 1px; box-shadow: 0 0 10px rgba(52, 211, 153, 0.2);">ALLOW</div>'
    elif result == "WARN":
        return '<div style="background-color: #78350f; color: #fbbf24; border: 1px solid #d97706; padding: 6px 18px; border-radius: 20px; font-weight: 700; display: inline-block; font-size: 14px; letter-spacing: 1px;">WARN</div>'
    elif result == "BLOCK":
        return '<div style="background-color: #7f1d1d; color: #f87171; border: 1px solid #dc2626; padding: 6px 18px; border-radius: 20px; font-weight: 700; display: inline-block; font-size: 14px; letter-spacing: 1px; box-shadow: 0 0 10px rgba(248, 113, 113, 0.2);">BLOCK</div>'
    else:  # ERROR
        return '<div style="background-color: #374151; color: #e5e7eb; border: 1px solid #4b5563; padding: 6px 18px; border-radius: 20px; font-weight: 700; display: inline-block; font-size: 14px; letter-spacing: 1px;">ERROR</div>'


with gr.Blocks(title="MCP-Consist") as demo:
    gr.Markdown("# MCP-Consist: Multi-Context Consistency Checker")


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)