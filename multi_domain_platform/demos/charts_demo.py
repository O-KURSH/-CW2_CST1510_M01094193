import pandas as pd
import streamlit as st 
import numpy as np
st.title("3. Charts Demo")
st.header("Line, area, and bar charts")
# Fake time series data
data = pd.DataFrame(
 np.random.randn(20, 3),
 columns=["A", "B", "C"]
)
st.subheader("Line chart")
st.line_chart(data)
st.subheader("Area chart")
st.area_chart(data)
st.subheader("Bar chart")
st.bar_chart(data)
st.divider()
st.header("Scatter chart & map")
# Scatter chart
scatter_data = pd.DataFrame(
 np.random.randn(100, 3),
 columns=["x", "y", "size"]
)
st.subheader("Scatter chart")
st.scatter_chart(scatter_data, x="x", y="y", size="size")
# Map (requires lat/lon columns)
st.subheader("Map")
map_data = pd.DataFrame({
 "lat": 51.5 + np.random.randn(100) * 0.01,
 "lon": -0.12 + np.random.randn(100) * 0.01,
})
st.map(map_data)
#If you want more control, you can use libraries like Altair, Matplotlib, or Plotly:
import altair as alt
st.header("Altair example")
chart = (
 alt.Chart(data.reset_index())
 .mark_line()
 .encode(
 x="index",
 y="A",
 )
)
st.altair_chart(chart, use_container_width=True)