# **Macroeconomic & Volatility Dashboard**

## **Overview**

The Macroeconomic & Volatility Dashboard is a real-time data visualization platform built with Python and Streamlit. It integrates with the Federal Reserve Economic Data (FRED) API to track and visualize correlations between interest rate policies, industrial/economic metrics, and market volatility markers.

The application features an automated Extract, Transform, Load (ETL) pipeline simulation, utilizing intelligent caching to periodically fetch live data while preventing API rate limits. For ease of demonstration, the app also includes a robust mock-data generator that activates automatically if no API key is provided.

## **Features**

* **Live FRED API Integration:** Fetches up-to-date monthly macroeconomic data directly from the St. Louis Fed.  
* **Automated ETL Pipeline:** Uses Streamlit's @st.cache\_data(ttl=3600) to simulate a scheduled data pipeline, caching results for one hour.  
* **Interactive Visualizations:** Powered by Plotly, including:  
  * Dual-axis time-series charts comparing interest rates and industrial metrics.  
  * Pearson correlation matrices to identify statistical relationships.  
  * Automated 6-month rolling volatility tracking.  
* **Smart Fallback Mechanism:** Automatically generates realistic, correlated mock data for instant previewing without API credentials.  
* **Dynamic KPIs:** Real-time calculation of metric changes (delta/basis points) over the selected timeframe.  
* **Secure API Key Management:** Utilizes Streamlit's built-in secrets manager (st.secrets) to securely load API credentials without hardcoding them into the repository.

## **Code Structure**

* **dashboard.py**: The main application file containing all logic and UI components.  
  * fetch\_fred\_data(): The core ETL function that calls the FRED API, cleanses the JSON response, handles missing values, and returns a formatted Pandas DataFrame.  
  * generate\_mock\_data(): A mathematical simulation function utilizing numpy to create correlated dummy data for demonstration purposes.  
  * **UI & Sidebar**: Uses Streamlit components (st.sidebar, st.columns, st.metric) to create an interactive layout for parameter tuning (dates, metrics, API key).

## **Installation & Setup**

1. **Clone the repository** (or download dashboard.py).  
2. **Install required dependencies:**  
   pip install streamlit pandas numpy requests plotly

3. **Set up your API Key (Recommended for Live Data):**  
   * Obtain a free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html).  
   * In your project directory, create a new folder named .streamlit.  
   * Inside that folder, create a file named secrets.toml.  
   * Add your API key to the secrets.toml file exactly like this:  
     FRED\_API\_KEY \= "your\_actual\_api\_key\_here"

   * **Important Security Step:** Add .streamlit/ to your .gitignore file to prevent your key from being exposed in version control.  
4. **Run the Streamlit application:**  
   streamlit run dashboard.py

5. **(Alternative) UI Input:**  
   * If you prefer not to use the secrets.toml file, you can simply run the app and paste your API key directly into the sidebar field.

## **Future Plans & Roadmap**

* **Advanced Predictive Analytics:** Integrate machine learning models (like ARIMA or Facebook Prophet) to forecast short-term movements in volatility based on leading rate indicators.  
* **Expanded Data Sources:** Incorporate additional APIs, such as Yahoo Finance (for granular equities data) and the Bureau of Labor Statistics (BLS), to broaden the macroeconomic picture.  
* **Robust ETL Orchestration:** Transition the in-memory Streamlit caching to a dedicated orchestration tool like Apache Airflow or Prefect for scheduled data warehouse ingestion.  
* **User Authentication & State Management:** Allow users to create accounts, save their preferred metric views, and set up email alerts for extreme volatility spikes.  
* **Cloud Deployment:** Containerize the application using Docker and deploy via AWS (ECS/Fargate) or Streamlit Community Cloud for public access.
