import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from taipy.gui import Gui, notify
import os

# --- 1. CLEANING DATA ---
def clean_val(x):
    if isinstance(x, str):
        x = x.replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
        return float(x) if x and x != '-' else 0.0
    return x

df = pd.read_csv('data/financial_data.csv')
df.columns = df.columns.str.strip()
for c in ['Sales', 'Profit', 'Units Sold', 'COGS']: df[c] = df[c].apply(clean_val)
df['Date'] = pd.to_datetime(df['Date'])

# --- 2. STATE & LOGIC ---
countries = sorted(list(df['Country'].unique()))
products = sorted(list(df['Product'].unique()))
segments = sorted(list(df['Segment'].unique()))

sel_country = countries
sel_product = products
sel_segment = segments

def get_filtered_data(c, p, s):
    return df[df['Country'].isin(c) & df['Product'].isin(p) & df['Segment'].isin(s)]

# Khởi tạo data ban đầu
f_df = get_filtered_data(sel_country, sel_product, sel_segment)

def on_change(state, var_name, var_value):
    if var_name in ["sel_country", "sel_product", "sel_segment"]:
        state.f_df = get_filtered_data(state.sel_country, state.sel_product, state.sel_segment)

# --- 3. CÁC TRANG BÁO CÁO ---

# TRANG 1: EXECUTIVE SUMMARY
page_summary = """
<|layout|columns=1 1 1 1|
<|part|class_name=card kpi-card|
**Total Sales** ## <|{f"${f_df['Sales'].sum():,.0f}"}|>
|>
<|part|class_name=card kpi-card|
**Net Profit** ## <|{f"${f_df['Profit'].sum():,.0f}"}|>
|>
<|part|class_name=card kpi-card|
**Units Sold** ## <|{f"{f_df['Units Sold'].sum():,.0f}"}|>
|>
<|part|class_name=card kpi-card|
**Margin %** ## <|{f"{(f_df['Profit'].sum()/f_df['Sales'].sum()*100) if f_df['Sales'].sum()>0 else 0:.1f}%"}|>
|>
|>

<|layout|columns=2 1|
<|part|class_name=card|
### **Sales & Profit Trend**
<|chart|figure={px.area(f_df.groupby('Date').sum().reset_index(), x='Date', y=['Sales', 'Profit'], color_discrete_sequence=['#0078d4', '#ff8c00'])}|>
|>
<|part|class_name=card|
### **Segment Distribution**
<|chart|figure={px.pie(f_df, values='Sales', names='Segment', hole=0.4)}|>
|>
|>
"""

# TRANG 2: REGIONAL ANALYSIS
page_region = """
<|layout|columns=1 1|
<|part|class_name=card|
### **World Sales Map**
<|chart|figure={px.choropleth(f_df.groupby('Country').sum().reset_index(), locations='Country', locationmode='country names', color='Sales', color_continuous_scale='Viridis')}|>
|>
<|part|class_name=card|
### **Profit by Country**
<|chart|figure={px.bar(f_df.groupby('Country').sum().reset_index(), x='Country', y='Profit', color='Country')}|>
|>
|>
<|layout|columns=1 1|
<|part|class_name=card|
### **Average Sale Price by Country**
<|chart|figure={px.box(f_df, x='Country', y='Sales', color='Country')}|>
|>
<|part|class_name=card|
### **Units vs Profit Scatter**
<|chart|figure={px.scatter(f_df, x='Units Sold', y='Profit', color='Product', size='Sales')}|>
|>
|>
"""

# TRANG 3: PRODUCT DEEP-DIVE
page_product = """
<|layout|columns=1 2|
<|part|class_name=card|
### **Product Sunburst**
<|chart|figure={px.sunburst(f_df, path=['Product', 'Segment'], values='Sales')}|>
|>
<|part|class_name=card|
### **Monthly Sales by Product**
<|chart|figure={px.line(f_df.groupby(['Date', 'Product']).sum().reset_index(), x='Date', y='Sales', color='Product')}|>
|>
|>
<|layout|columns=1 1|
<|part|class_name=card|
### **COGS vs Sales**
<|chart|figure={px.bar(f_df.groupby('Product').sum().reset_index(), x='Product', y=['Sales', 'COGS'], barmode='group')}|>
|>
<|part|class_name=card|
### **Discount Impact**
<|chart|figure={px.violin(f_df, x='Product', y='Profit', color='Discount Band', box=True)}|>
|>
|>
"""

# TRANG 4: DATA EXPLORER
page_data = """
<|part|class_name=card|
### **Master Data Table**
<|{f_df}|table|page_size=15|filter=True|>
|>
"""

# --- 4. MAIN LAYOUT (SIDEBAR + CONTENT) ---
root_md = """
<|layout|columns=280px 1|
<|part|class_name=sidebar|
# **BI PANEL**
---
**GLOBAL FILTERS**
<br/>
<|{sel_country}|selector|lov={countries}|multiple|dropdown|label=🌍 Countries|>
<br/>
<|{sel_product}|selector|lov={products}|multiple|dropdown|label=📦 Products|>
<br/>
<|{sel_segment}|selector|lov={segments}|multiple|dropdown|label=🏢 Segments|>
<br/>
---
<br/>
<|XUẤT EXCEL|button|class_name=taipy-button|>
|>

<|part|class_name=main-container|
<|part|class_name=navbar-container|
<center><|navbar|></center>
|>
<|content|>
|>
|>
"""

pages = {
    "/": root_md,
    "Executive-Summary": page_summary,
    "Regional-Analytics": page_region,
    "Product-Deep-Dive": page_product,
    "Data-Explorer": page_data
}

if __name__ == "__main__":
   
    port = int(os.environ.get("PORT", 5000))
    
    Gui(pages=pages).run(
        title="Enterprise BI Dashboard",
        css_file="assets/custom.css",
        viewport_width="100%",
        dark_mode=False,
        
        host="0.0.0.0", 
        port=port

    )
