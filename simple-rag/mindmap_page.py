import streamlit as st

def render_mindmap(mindmap_desc):
    st.markdown(
        f"""
        <div id="mindmap"></div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ startOnLoad: true }});
            document.getElementById('mindmap').innerHTML = `\`\`\`mermaid
            {mindmap_desc}
            \`\`\``;
            mermaid.contentLoaded();
        </script>
        """,
        unsafe_allow_html=True
    )

def page():
    st.header("MindMap Creator")

    mindmap_desc = st.text_area("MindMap Description", height=200, value="graph LR\n    A --- B\n    B-->C[fa:fa-ban forbidden]\n    B-->D(fa:fa-spinner);")
    if st.button("Render MindMap"):
        if mindmap_desc.strip():
            render_mindmap(mindmap_desc)
        else:
            st.error("MindMap Description cannot be empty")

if __name__ == "__main__":
    page()