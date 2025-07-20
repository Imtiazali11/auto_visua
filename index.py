import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
import time
import os

# Page configuration
st.set_page_config(
    page_title="AutoViz Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .sidebar .sidebar-content {
        background: #1a1a2e;
        color: white;
    }
    .stProgress > div > div > div > div {
        background-color: #4e73df;
    }
    .st-bb {
        background-color: transparent;
    }
    .st-at {
        background-color: #0c0f24;
    }
    footer {
        visibility: hidden;
    }
    .plot-title {
        font-size: 16px !important;
        font-weight: 600 !important;
        margin-top: 10px !important;
        margin-bottom: 5px !important;
    }
</style>
""", unsafe_allow_html=True)

def load_data(uploaded_file):
    """Load data from uploaded file"""
    try:
        if uploaded_file.name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def analyze_data(df):
    """Categorize columns by data type"""
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []
    
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)
        else:
            # Treat as categorical if reasonable number of unique values
            if df[col].nunique() <= 20:
                categorical_cols.append(col)
    
    return numeric_cols, categorical_cols, datetime_cols

def generate_visualizations(df, numeric_cols, categorical_cols, datetime_cols):
    """Generate visualizations and return plot objects"""
    plots = []
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Univariate plots
    total_plots = len(numeric_cols)*2 + len(categorical_cols) + len(datetime_cols)*min(1, len(numeric_cols))
    if len(numeric_cols) > 1:
        total_plots += 2  # Heatmap and pairplot
    
    plot_counter = 0
    
    # Histograms for numeric columns
    for i, col in enumerate(numeric_cols):
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(df[col], kde=True, ax=ax)
        ax.set_title(f'Distribution of {col}', fontsize=14)
        ax.set_xlabel(col)
        plots.append(("histogram", fig, col))
        plt.close(fig)
        
        plot_counter += 1
        progress_bar.progress(plot_counter/total_plots)
        status_text.text(f"Generated {plot_counter}/{total_plots} visualizations...")
    
    # Boxplots for numeric columns
    for i, col in enumerate(numeric_cols):
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.boxplot(x=df[col], ax=ax)
        ax.set_title(f'Boxplot of {col}', fontsize=14)
        plots.append(("boxplot", fig, col))
        plt.close(fig)
        
        plot_counter += 1
        progress_bar.progress(plot_counter/total_plots)
        status_text.text(f"Generated {plot_counter}/{total_plots} visualizations...")
    
    # Bar plots for categorical columns
    for i, col in enumerate(categorical_cols):
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.countplot(y=col, data=df, order=df[col].value_counts().index, ax=ax)
        ax.set_title(f'Distribution of {col}', fontsize=14)
        ax.set_xlabel('Count')
        plots.append(("barplot", fig, col))
        plt.close(fig)
        
        plot_counter += 1
        progress_bar.progress(plot_counter/total_plots)
        status_text.text(f"Generated {plot_counter}/{total_plots} visualizations...")
    
    # Correlation heatmap
    if len(numeric_cols) > 1:
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', ax=ax)
        ax.set_title('Feature Correlation Matrix', fontsize=14)
        plots.append(("heatmap", fig, "Correlation"))
        plt.close(fig)
        
        plot_counter += 1
        progress_bar.progress(plot_counter/total_plots)
        status_text.text(f"Generated {plot_counter}/{total_plots} visualizations...")
    
    # Pairplot (sample if large dataset)
    if len(numeric_cols) > 1:
        pairplot = sns.pairplot(df[numeric_cols].sample(min(500, len(df))))
        fig = pairplot.figure
        plots.append(("pairplot", fig, "Pairwise Relationships"))
        plt.close(fig)
        
        plot_counter += 1
        progress_bar.progress(plot_counter/total_plots)
        status_text.text(f"Generated {plot_counter}/{total_plots} visualizations...")
    
    # Time series plots
    for date_col in datetime_cols:
        if len(numeric_cols) > 0:
            num_col = numeric_cols[0]  # Use first numeric column
            fig, ax = plt.subplots(figsize=(12, 6))
            df.set_index(date_col)[num_col].plot(ax=ax)
            ax.set_title(f'{num_col} over Time', fontsize=14)
            ax.set_ylabel(num_col)
            plots.append(("timeseries", fig, f"{date_col} & {num_col}"))
            plt.close(fig)
            
            plot_counter += 1
            progress_bar.progress(plot_counter/total_plots)
            status_text.text(f"Generated {plot_counter}/{total_plots} visualizations...")
    
    progress_bar.empty()
    status_text.empty()
    
    return plots

def create_zip_archive(plots):
    """Create a ZIP file of all visualizations"""
    import zipfile
    from io import BytesIO
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for i, (plot_type, fig, col) in enumerate(plots):
            img_buffer = BytesIO()
            fig.savefig(img_buffer, format='png', bbox_inches='tight')
            img_buffer.seek(0)
            zip_file.writestr(f"plot_{i+1}_{plot_type}_{col.replace(' ', '_')}.png", img_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer

# Main App
st.title("📊 AutoViz Pro - Automated Data Visualization By Imtiaz Ali")
st.markdown("Upload your dataset and get automatic visualizations in seconds!")

with st.sidebar:
    st.header("Configuration")
    uploaded_file = st.file_uploader("Upload Dataset (CSV or Excel)", type=['csv', 'xlsx'])
    
    st.markdown("---")
    st.subheader("About")
    st.markdown("""
    This tool automatically analyzes your dataset and generates:
    - Distribution plots
    - Correlation matrices
    - Time series charts
    - Categorical distributions
    """)
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit")

if uploaded_file is not None:
    df = load_data(uploaded_file)
    
    if df is not None:
        st.success(f"Successfully loaded dataset with {df.shape[0]} rows and {df.shape[1]} columns")
        
        with st.expander("View Raw Data"):
            st.dataframe(df.head())
        
        numeric_cols, categorical_cols, datetime_cols = analyze_data(df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Numerical Columns", len(numeric_cols))
        col2.metric("Categorical Columns", len(categorical_cols))
        col3.metric("Date/Time Columns", len(datetime_cols))
        
        if st.button("Generate Visualizations", use_container_width=True):
            with st.spinner("Analyzing data and creating visualizations..."):
                plots = generate_visualizations(df, numeric_cols, categorical_cols, datetime_cols)
                
            st.success("Visualization complete!")
            st.balloons()
            
            # Display plots in organized tabs
            tab1, tab2, tab3, tab4 = st.tabs(["Distributions", "Relationships", "Time Series", "All Plots"])
            
            with tab1:
                st.subheader("Distribution Plots")
                cols = st.columns(2)
                for i, (plot_type, fig, col_name) in enumerate(plots):
                    if plot_type in ['histogram', 'boxplot', 'barplot']:
                        with cols[i % 2]:
                            st.markdown(f'<p class="plot-title">{col_name}</p>', unsafe_allow_html=True)
                            st.pyplot(fig)
            
            with tab2:
                st.subheader("Relationship Analysis")
                for plot_type, fig, col_name in plots:
                    if plot_type in ['heatmap', 'pairplot']:
                        st.markdown(f'<p class="plot-title">{col_name}</p>', unsafe_allow_html=True)
                        st.pyplot(fig)
            
            with tab3:
                st.subheader("Time Series Analysis")
                for plot_type, fig, col_name in plots:
                    if plot_type == 'timeseries':
                        st.markdown(f'<p class="plot-title">{col_name}</p>', unsafe_allow_html=True)
                        st.pyplot(fig)
            
            with tab4:
                st.subheader("All Generated Visualizations")
                for plot_type, fig, col_name in plots:
                    st.markdown(f'<p class="plot-title">{col_name} ({plot_type.capitalize()})</p>', unsafe_allow_html=True)
                    st.pyplot(fig)
            
            # Download options
            st.markdown("---")
            st.subheader("Download Results")
            
            # ZIP Download
            zip_buffer = create_zip_archive(plots)
            st.download_button(
                label="Download All Visualizations (ZIP)",
                data=zip_buffer,
                file_name="autoviz_report.zip",
                mime="application/zip",
                use_container_width=True
            )
            
            # HTML Report
            html_report = "<html><body><h1>AutoViz Report</h1>"
            for plot_type, fig, col_name in plots:
                img_buffer = BytesIO()
                fig.savefig(img_buffer, format='png', bbox_inches='tight')
                img_str = base64.b64encode(img_buffer.getvalue()).decode()
                html_report += f"<h2>{col_name} ({plot_type})</h2>"
                html_report += f'<img src="data:image/png;base64,{img_str}"><br>'
            html_report += "</body></html>"
            
            st.download_button(
                label="Download HTML Report",
                data=html_report,
                file_name="autoviz_report.html",
                mime="text/html",
                use_container_width=True
            )
else:
    st.info("Please upload a dataset to get started")
    st.image("https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1200&q=80", 
             caption="Data Visualization Made Simple")