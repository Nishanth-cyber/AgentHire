# Multi-Agent Resume ATS Analyzer

A Streamlit mini-project demonstrating six specialized AI agents and four communication architectures: Sequential, Parallel, Blackboard/Shared State, and Peer-to-Peer (Fixed/Dynamic).

## Stack
- Python
- Streamlit
- LangChain + `langchain-huggingface`
- Hugging Face Serverless Inference API (Free Cloud) or Ollama (Local)
- PyMuPDF
- ReportLab

## Local Run
1. Install dependencies: `pip install -r requirements.txt`
2. Run: `streamlit run app.py`
3. In the sidebar:
   - Choose **Hugging Face (Free Cloud)**: Select a model (e.g. `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` or `Qwen/Qwen2.5-7B-Instruct`) and enter your token or set it in `.env`.
   - Or choose **Ollama (Local)**: Run `ollama pull qwen3:4b` locally.

## Deploy to Streamlit Community Cloud
1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and click **New app**.
3. Select your repository, branch (`main`), and set **Main file path** to `app.py`.
4. Under **Advanced settings -> Secrets**, paste the following:
   ```toml
   HF_TOKEN = "your_huggingface_token_here"
   HF_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
   LLM_PROVIDER = "Hugging Face"
   ```
5. Click **Deploy!**

## Download
After analysis, use **Download ATS Report** to download a generated PDF directly from the Streamlit UI.

