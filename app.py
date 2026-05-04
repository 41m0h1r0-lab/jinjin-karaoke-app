#streamlit実装
import streamlit as st
import pandas as pd
import plotly.express as px

# ページの設定
st.set_page_config(page_title="Jinjin's Karaoke Analytics", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("cleaned_karaoke_data.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# --- サイドバー：フィルタリング機能（復活！） ---
st.sidebar.header("🔍 絞り込みフィルター")

# 1. 期間選択
min_date = df['date'].min().date()
max_date = df['date'].max().date()
date_range = st.sidebar.date_input("歌唱期間を選択", [min_date, max_date])

# 2. アーティスト多重選択
all_artists = sorted(df['artist'].unique())
selected_artists = st.sidebar.multiselect("アーティストを選択（複数可）", all_artists)

# 3. ジャンル選択
all_genres = df['genre'].unique()
selected_genres = st.sidebar.multiselect("ジャンルを選択", all_genres, default=all_genres)

# --- フィルタリングの実行 ---
# ジャンルで絞り込み
mask = df['genre'].isin(selected_genres)

# アーティストで絞り込み（選択されている場合のみ）
if selected_artists:
    mask = mask & df['artist'].isin(selected_artists)

# 日付で絞り込み
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = mask & (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)

filtered_df = df[mask]

# --- メインコンテンツ ---
st.title("🎤 じんじんのカラオケ歌唱記録🧸 ")

# 指標表示
m1, m2, m3, m4 = st.columns(4)
m1.metric("総歌唱回数", len(filtered_df))
m2.metric("ユニーク曲数（曲名の数）", filtered_df['song'].nunique())
m3.metric("最多アーティスト", filtered_df['artist'].mode()[0] if not filtered_df.empty else "-")
m4.metric("平均キー変更", f"{filtered_df['key_num'].mean():+.1f}" if not filtered_df.empty else "0.0")

st.divider()

# --- キー変更が必要な曲（固定表示） ---
# フィルタリング後のデータから、キー調整(0以外)がある曲を抽出
st.subheader("📌 キー調整が必要な曲リスト (現在の条件内)")
key_adjusted_df = filtered_df[filtered_df['key_num'] != 0].copy()

if not key_adjusted_df.empty:
    # 曲ごとに「最も頻繁に設定するキー」を算出
    key_summary = key_adjusted_df.groupby(['song', 'artist'])['key_num'].agg(
        lambda x: x.value_counts().index[0]
    ).reset_index()
    key_summary.columns = ['曲名', 'アーティスト', 'おすすめ設定キー']
    st.dataframe(key_summary, use_container_width=True, height=200)
else:
    st.info("選択された条件の中に、キー調整された曲はありません。")

st.divider()

# --- タブエリア ---
tab1, tab2, tab3 = st.tabs(["🏆 ランキング分析", "📊 傾向・分布", "📋 全データ詳細"])

with tab1:
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("アーティスト別 TOP 20")
        top_art = filtered_df['artist'].value_counts().head(20).reset_index()
        top_art.columns = ['artist', 'count']
        fig_art = px.bar(top_art, x='count', y='artist', orientation='h', 
                         color='count', color_continuous_scale='Viridis')
        fig_art.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_art, use_container_width=True)

    with col_right:
        st.subheader("曲別歌唱数 TOP 20")
        # アーティスト名も保持して集計
        top_song = filtered_df.groupby(['song', 'artist']).size().reset_index(name='count')
        top_song = top_song.sort_values('count', ascending=False).head(20)
        
        fig_song = px.bar(top_song, x='count', y='song', orientation='h', 
                          color='count', color_continuous_scale='Reds',
                          hover_data=['artist'])
        fig_song.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_song, use_container_width=True)

with tab2:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📅 月別歌唱トレンド")
        if not filtered_df.empty:
            df_trend = filtered_df.copy()
            df_trend['month'] = df_trend['date'].dt.to_period('M').astype(str)
            trend_data = df_trend.groupby('month').size().reset_index(name='歌唱数')
            st.plotly_chart(px.line(trend_data, x='month', y='歌唱数', markers=True), use_container_width=True)
    with c2:
        st.subheader("⏳ リリース年代の分布")
        st.plotly_chart(px.histogram(filtered_df, x='year'), use_container_width=True)

with tab3:
    st.subheader("📋 歌唱履歴一覧")
    # 検索機能付きのテーブル
    st.dataframe(filtered_df[['date', 'song', 'artist', 'genre', 'year', 'key_num']].sort_values('date', ascending=False), 
                 use_container_width=True)