# Documentation

## Generation

1. Install [Quarto](https://quarto.org/docs/get-started/)
1. From this (docs) directory, run the following commands:

    ```
    ../src/odm_validation/tools/render_quarto_docs.py
    pip install -r ./requirements.txt
    make html
    ```

1. Open `file://<repo_path>/docs/build/html/index.html` in your browser.
