# Deploying to Streamlit Cloud

Here is how to get your LLC Design Sweeper tool running on the web.

## 1. Prepare GitHub Repository
Streamlit Cloud runs code directly from GitHub. You need to put this folder into a GitHub repository.

1.  **Create a New Repository** on [GitHub.com](https://github.com/new).
2.  **Push your code** to it. In your terminal:
    ```bash
    git init
    git add .
    git commit -m "Initial commit of LLC Sweeper App"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    git push -u origin main
    ```

## 2. Deploy on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Log in with GitHub.
3.  Click **"New app"**.
4.  **Configuration**:
    *   **Repository**: Select your new repo (`YOUR_USERNAME/YOUR_REPO_NAME`).
    *   **Branch**: `main`.
    *   **Main file path**: `streamlit_app.py`.
5.  Click **"Deploy!"**.

## 3. Troubleshooting
*   **Dependencies**: Streamlit Cloud will automatically look for `requirements.txt` and install the libraries listed there (`pandas`, `numpy`, `scipy`, etc.).
*   **Import Errors**: The app includes special logic to find the local `src` folder. If you see "Module not found", ensure your folder structure on GitHub usually looks like this:
    ```
    repo-name/
    ├── requirements.txt
    ├── streamlit_app.py
    └── src/
        └── llc_sweeper/
            ├── __init__.py
            ├── models.py
            ├── ...
    ```
