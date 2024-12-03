# Documentation

## Generation

1. Install [Quarto](https://quarto.org/docs/get-started/)
1. From the repo root directory, run the following commands:

    ```
    python3 tools/render_quarto_docs.py
    cd docs
    pip install -r requirements.txt
    make html
    ```

1. Open `file://<repo_path>/docs/build/html/index.html` in your browser.
