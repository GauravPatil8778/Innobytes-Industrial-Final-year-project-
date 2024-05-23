import streamlit as st
import requests

def fetch_news(api_url):
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json().get("results", [])
        else:
            st.warning(f"Failed to fetch news. Status code: {response.status_code}")
            return []
    except Exception as e:
        st.warning(f"An error occurred while fetching news: {str(e)}")
        return []

def display_news(articles):
    for index, article in enumerate(articles):
        title = article.get("title", "")
        description = article.get("description", "")
        source = article.get("source_id", "")
        published_at = article.get("pubDate", "")
        url = article.get("link", "")
        image_url = article.get("image_url", "")

        col1, col2 = st.columns([1, 2])

        with col1:
            if image_url:
                st.image(image_url, caption="Image", use_column_width=True)

        with col2:
            st.subheader(title)
            st.write(description)
            st.write(f"Source: {source} - Published: {published_at}")

            button_key = f"read_more_{index}"
            if st.button("Read More", key=button_key):
                st.markdown(f"[Read the full article]({url})")
        st.markdown('---')

def app():
    st.title("News Dashboard")

    api_key = "pub_445380a6a2d3edb39bb2e150574c6b7f09895"
    commodities_api_url = f"https://newsdata.io/api/1/news?apikey={api_key}&q=Commodities&language=en"

    st.header("Commodities News")
    commodities_articles = fetch_news(commodities_api_url)
    display_news(commodities_articles)

if __name__ == "__main__":
    app()
