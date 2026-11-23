# De Buurtwinkel — auto-loading Streamlit dashboard

This is a **Streamlit recreation** of `DeBuurtwinkel.pbit`, **not** a Power BI renderer. Once you add the original CSV files, everyone opening your deployed Streamlit URL will immediately see the interactive dashboard, with no upload step and no Power BI login.

## 1. Add your data (essential)

The Power BI `.pbit` template contains no sales records. Copy these **original** files from your computer (previously referenced by the template from a `Downloads\PBI` folder) into this project's `data/` directory:

```text
debuurtwinkel_streamlit_autoload/
  app.py
  requirements.txt
  data/
    sales_data.csv
    product_details.csv
    store_locations.csv
  assets/
    supermarket_banner.jpg
```

The column names need to match:

| File | Required columns |
| --- | --- |
| sales_data.csv | TransactionID, Date, ProductID, StoreID, UnitsSold |
| product_details.csv | ProductID, ProductName, ProductCategory, UnitPrice, UnitCost |
| store_locations.csv | StoreID, City, Province |

You can use `python verify_data.py` to check filenames and headers before deploying.

**Privacy:** If you upload these CSVs into a **public GitHub repository**, anyone may download the original data. Only do so if the data is cleared for public release. If it is private, do not use this public-data setup.

## 2. Run on your own computer

In VS Code, open this folder, then in PowerShell:

```powershell
python -m pip install -r requirements.txt
python verify_data.py
python -m streamlit run app.py
```

Open http://localhost:8501. You do **not** need Node.js or npm.

## 3. Deploy with Streamlit Community Cloud

1. Create a GitHub repository (only make it public if the dataset is public).
2. Upload everything inside this folder — the Python files, `requirements.txt`, the `assets` directory, and **your three CSVs inside `data/`**.
3. Sign in at https://share.streamlit.io/ with GitHub.
4. Create an app from that repository, choose branch `main`, and set **Main file path** to `app.py`.
5. Click **Deploy**.

Visitors will immediately see the dashboards, charts, slicers and KPIs without uploading files. The **original** `.pbit` file does not need to be deployed.

### Important notes

- The CSVs are **not included** in this ZIP, because they were never provided. The app shows a clear missing-files message until you supply them.
- This dashboard is a translation of the Power BI design, not pixel-perfect, and year-over-year figures are an approximation of DAX date context.
- The app does not expose a download of individual transaction rows by default. This does not replace securing the data source.
- Changes to the CSVs require committing the updated data to GitHub and redeploying/rebooting the app.
