# dashboard/app.py - Complete Streamlit dashboard
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import requests

# Page config
st.set_page_config(
    page_title="RAG Evaluation Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .good { color: #00ff00; }
    .bad { color: #ff0000; }
</style>
""", unsafe_allow_html=True)

class RAGDashboard:
    def __init__(self):
        self.api_url = "http://localhost:8000"
    
    def load_metrics(self):
        """Load metrics from evaluation results"""
        try:
            with open("evaluation_results/latest_metrics.json", "r") as f:
                return json.load(f)
        except:
            return self.get_mock_metrics()
    
    def get_mock_metrics(self):
        """Mock metrics for demo"""
        return {
            "recall@5": 0.85,
            "recall@10": 0.92,
            "mrr": 0.88,
            "ndcg@10": 0.86,
            "faithfulness": 0.91,
            "answer_relevancy": 0.89,
            "context_precision": 0.87,
            "latency_p95": 145,
            "cost_per_query": 0.008
        }
    
    def render_header(self):
        st.title("🔍 RAG Pipeline Evaluation Dashboard")
        st.markdown("Real-time monitoring of retrieval and generation quality")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Queries", "1,234", "+12%")
        with col2:
            st.metric("Avg Latency", "145ms", "-8ms")
        with col3:
            st.metric("Cost Today", "$12.34", "+$2.10")
    
    def render_metrics_overview(self, metrics):
        st.subheader("📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            recall = metrics.get('recall@5', 0)
            color = "good" if recall > 0.8 else "bad"
            st.markdown(f"""
            <div class="metric-card">
                <h4>Recall@5</h4>
                <h2 class="{color}">{recall:.3f}</h2>
                <small>Threshold: 0.80</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            mrr = metrics.get('mrr', 0)
            color = "good" if mrr > 0.75 else "bad"
            st.markdown(f"""
            <div class="metric-card">
                <h4>MRR</h4>
                <h2 class="{color}">{mrr:.3f}</h2>
                <small>Threshold: 0.75</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            faithfulness = metrics.get('faithfulness', 0)
            color = "good" if faithfulness > 0.85 else "bad"
            st.markdown(f"""
            <div class="metric-card">
                <h4>Faithfulness</h4>
                <h2 class="{color}">{faithfulness:.3f}</h2>
                <small>Threshold: 0.85</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            latency = metrics.get('latency_p95', 0)
            color = "good" if latency < 200 else "bad"
            st.markdown(f"""
            <div class="metric-card">
                <h4>P95 Latency</h4>
                <h2 class="{color}">{latency:.0f}ms</h2>
                <small>Target: &lt;200ms</small>
            </div>
            """, unsafe_allow_html=True)
    
    def render_performance_charts(self, metrics):
        st.subheader("📈 Performance Trends")
        
        # Time series data
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        trend_data = pd.DataFrame({
            'date': dates,
            'recall@5': [metrics.get('recall@5', 0.85) + (i * 0.001) for i in range(30)],
            'recall@10': [metrics.get('recall@10', 0.90) + (i * 0.0005) for i in range(30)]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=trend_data['date'], y=trend_data['recall@5'], 
                                  name='Recall@5', mode='lines+markers'))
        fig.add_trace(go.Scatter(x=trend_data['date'], y=trend_data['recall@10'], 
                                  name='Recall@10', mode='lines+markers'))
        fig.update_layout(title='Retrieval Quality Over Time', xaxis_title='Date', 
                          yaxis_title='Score', height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_cost_analysis(self, metrics):
        st.subheader("💰 Cost Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cost_data = pd.DataFrame({
                'Component': ['Embedding', 'Retrieval', 'Reranking', 'Generation'],
                'Cost ($)': [0.012, 0.001, 0.008, 0.045]
            })
            fig = px.bar(cost_data, x='Component', y='Cost ($)', 
                         title='Cost Breakdown per Query', color='Component')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.metric("Cost per Query", f"${metrics.get('cost_per_query', 0.01):.4f}", 
                      "-$0.002", delta_color="normal")
            st.metric("Daily Cost (10k queries)", f"${metrics.get('cost_per_query', 0.01) * 10000:.2f}")
            st.metric("Monthly Projection", f"${metrics.get('cost_per_query', 0.01) * 10000 * 30:.2f}")
    
    def render_query_explorer(self):
        st.subheader("🔍 Query Explorer")
        
        query = st.text_input("Enter a test query:", "What is hybrid search in RAG?")
        
        if st.button("Search"):
            with st.spinner("Searching..."):
                try:
                    response = requests.post(f"{self.api_url}/v1/search", 
                                            json={"query": query, "top_k": 5})
                    results = response.json()
                    
                    st.success(f"Found {len(results.get('documents', []))} results in {results.get('latency_ms', 0)}ms")
                    
                    for i, doc in enumerate(results.get('documents', []), 1):
                        with st.expander(f"Result {i}: Score {doc.get('score', 0):.3f}"):
                            st.markdown(f"**Source:** {doc.get('source', 'Unknown')}")
                            st.markdown(f"**Text:** {doc.get('text', '')[:500]}...")
                            
                            if 'citations' in doc:
                                st.markdown(f"**Citations:** {doc['citations']}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    def render_worst_queries(self):
        st.subheader("📉 Worst Performing Queries")
        
        worst_queries = pd.DataFrame({
            'Query': ['What is BM25?', 'How to implement RRF?', 'Explain dense retrieval'],
            'Recall@5': [0.45, 0.52, 0.61],
            'Latency (ms)': [234, 189, 156],
            'Improvement Needed': ['High', 'Medium', 'Low']
        })
        
        st.dataframe(worst_queries, use_container_width=True)
        
        st.markdown("### 📝 Improvement Suggestions")
        for _, row in worst_queries.iterrows():
            if row['Improvement Needed'] == 'High':
                st.warning(f"**{row['Query']}** - Consider adding query expansion or domain-specific embeddings")
    
    def run(self):
        metrics = self.load_metrics()
        
        self.render_header()
        self.render_metrics_overview(metrics)
        self.render_performance_charts(metrics)
        
        tab1, tab2, tab3 = st.tabs(["Cost Analysis", "Query Explorer", "Troubleshooting"])
        
        with tab1:
            self.render_cost_analysis(metrics)
        with tab2:
            self.render_query_explorer()
        with tab3:
            self.render_worst_queries()

if __name__ == "__main__":
    dashboard = RAGDashboard()
    dashboard.run()