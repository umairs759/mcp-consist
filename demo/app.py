import gradio as gr
from pipeline import run_consistency_check


def run_check(input_text1, input_text2, threshold):
    """Run consistency check and return HTML badge snippet."""
    result = run_consistency_check(input_text1, input_text2, threshold)

    # Map result to badge class
    if result == "ALLOW":
        badge_class = "badge badge-allow"
    elif result == "WARN":
        badge_class = "badge badge-warn"
    elif result == "BLOCK":
        badge_class = "badge badge-block"
    else:
        badge_class = "badge badge-error"

    # Return well-formed HTML snippet for the badge
    return f'<div style="display:flex; align-items:center;"><span class="{badge_class}">{result}</span></div>'


with gr.Blocks(title="MCP-Consist") as demo:
    gr.Markdown("# MCP-Consist: Multi-Context Consistency Checker")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Inputs")
            input1 = gr.Textbox(label="Input 1", placeholder="Enter first context...")
            input2 = gr.Textbox(label="Input 2", placeholder="Enter second context...")
            threshold = gr.Slider(
                minimum=0.0,
                maximum=1.0,
                value=0.5,
                step=0.01,
                label="Threshold",
            )

            with gr.Row():
                run_btn = gr.Button("Run Consistency Check", variant="primary")
                clear_btn = gr.ClearButton(components=[input1, input2, threshold])

        with gr.Column(scale=1):
            gr.Markdown("### Results")
            status_badge = gr.HTML(label="Status Badge")

    # CSS for badge styling
    gr.Markdown(
        """
        <style>
        /* Badge styles for consistency status */
        .badge-allow {
            background: #064e3b;
            color: #34d399;
            border: 1px solid #059669;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        .badge-warn {
            background: #78350f;
            color: #fbbf24;
            border: 1px solid #d97706;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        .badge-block {
            background: #7f1d1d;
            color: #f87171;
            border: 1px solid #dc2626;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        .badge-error {
            background: #374151;
            color: #e5e7eb;
            border: 1px solid #4b5563;
            padding: 6px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }
        /* Ensure badges render as inline-block within the flex container */
        .badge {
            display: inline-block;
            margin: 4px;
        }
        </style>
        """
    )

    # Wire up the run button
    run_btn.click(
        fn=run_check,
        inputs=[input1, input2, threshold],
        outputs=[status_badge],
    )


if __name__ == "__main__":
    demo.launch()