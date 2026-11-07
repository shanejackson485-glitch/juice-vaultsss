import os
import random
import html
import requests
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Juice WRLD Vault",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API = os.getenv(
    "VAULT_API_URL",
    "https://juicewrld.io/api/v1"
).rstrip("/")

API_KEY = os.getenv("VAULT_API_KEY")

HEADERS = {}
if API_KEY:
    HEADERS["X-API-Key"] = API_KEY


# ============================================================
# STYLING
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top right, #172b4c 0%, transparent 35%),
        linear-gradient(135deg, #080a10, #111722 55%, #090b11);
    color: #e8edf7;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1500px;
}

.brand {
    font-size: 29px;
    font-weight: 800;
    color: white;
    letter-spacing: -1.2px;
}

.muted {
    color: #91a0b5;
}

.hero {
    padding: 38px;
    border: 1px solid #26364e;
    border-radius: 22px;
    background:
        linear-gradient(
            110deg,
            rgba(37,99,235,.25),
            rgba(15,23,42,.65)
        );
    margin: 18px 0 25px;
}

.hero h1 {
    font-size: 42px;
    color: white;
    font-weight: 800;
    margin: 8px 0;
}

.card {
    background: #121925;
    border: 1px solid #263244;
    border-radius: 15px;
    padding: 16px;
    margin-bottom: 12px;
}

div[data-testid="stMetric"] {
    background: #121925;
    border: 1px solid #263244;
    padding: 16px;
    border-radius: 14px;
}

.stButton > button {
    border-radius: 10px;
    border: 1px solid #334155;
    background: #17263d;
    color: white;
    transition: .2s;
}

.stButton > button:hover {
    border-color: #3b82f6;
    color: white;
}

section[data-testid="stSidebar"] {
    background: #0b1019;
    border-right: 1px solid #202b3d;
}

a {
    color: #60a5fa !important;
}

div[data-testid="stImage"] img {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# API HELPERS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def api_get(path, params=None):

    url = f"{API}/{path.lstrip('/')}"

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return response.json()


def unwrap(response):

    if isinstance(response, dict):
        return response.get("data", response)

    return response


def get_data(path, params=None):

    try:
        return unwrap(api_get(path, params))

    except requests.exceptions.HTTPError as error:

        status = error.response.status_code if error.response else "Unknown"

        st.error(
            f"API returned HTTP {status}. "
            "Check the requested endpoint or parameters."
        )

    except requests.exceptions.ConnectionError:

        st.error(
            "Could not connect to the Juice WRLD catalogue API."
        )

    except requests.exceptions.Timeout:

        st.error("The API request timed out.")

    except Exception as error:

        st.error(f"Unexpected API error: {error}")

    return None


def safe_text(value, fallback="Unknown"):

    if value is None or value == "":
        return fallback

    return str(value)


def open_link(url):

    if url and isinstance(url, str):
        st.link_button("Open on Juice WRLD", url)


def show_cover(url, width=180):

    if url:
        try:
            st.image(url, width=width)
        except Exception:
            st.caption("Artwork unavailable.")


def show_song(song):

    title = safe_text(song.get("title"))
    status = safe_text(song.get("status"), "unknown").upper()
    era = safe_text(song.get("era"), "Unknown era")
    duration = song.get("duration") or {}
    duration_text = duration.get("text", "Unknown length")

    with st.container(border=True):

        left, right = st.columns([1, 5])

        with left:
            show_cover(song.get("cover"), 110)

        with right:

            st.markdown(f"### {title}")

            st.caption(
                f"{status} · {era} · {duration_text}"
            )

            if song.get("versionLabel"):
                st.caption(song["versionLabel"])

            if song.get("url"):
                st.link_button(
                    "View song page ↗",
                    song["url"]
                )

            if song.get("hasAudio"):
                st.caption("🎧 Audio available on the catalogue website.")


def show_song_details(song_id):

    song = get_data(f"/songs/{song_id}")

    if not isinstance(song, dict):
        st.warning("Song details could not be loaded.")
        return

    st.divider()

    st.subheader("Song information")

    left, right = st.columns([1, 3])

    with left:
        show_cover(song.get("cover"), 220)

    with right:

        st.title(song.get("title", "Unknown"))

        st.caption(
            f"{safe_text(song.get('status')).upper()} "
            f"· {safe_text(song.get('eraName'))}"
        )

        if song.get("url"):
            open_link(song["url"])

        st.write(
            f"**Duration:** "
            f"{(song.get('duration') or {}).get('text', 'Unknown')}"
        )

        st.write(f"**BPM:** {safe_text(song.get('bpm'))}")
        st.write(f"**Key:** {safe_text(song.get('key'))}")
        st.write(f"**Location:** {safe_text(song.get('location'))}")

    dates = song.get("dates") or {}

    st.subheader("Dates")

    a, b, c, d = st.columns(4)

    for column, label in zip(
        [a, b, c, d],
        ["Recorded", "Previewed", "Released", "Surfaced"]
    ):

        date = dates.get(label.lower()) or {}

        column.metric(
            label,
            date.get("text", "Unknown")
        )

    credits = song.get("credits") or {}

    st.subheader("Credits")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("**Producers**")

        for person in credits.get("producers", []):
            st.write(f"• {person.get('name', 'Unknown')}")

    with col2:

        st.markdown("**Engineers**")

        for person in credits.get("engineers", []):
            st.write(f"• {person.get('name', 'Unknown')}")

    notes = song.get("notes") or []

    if notes:

        st.subheader("Notes")

        for note in notes:
            st.write(f"• {note}")

    versions = song.get("versions") or []

    if versions:

        st.subheader("Versions")

        for version in versions:
            show_song(version)


# ============================================================
# NAVIGATION
# ============================================================

PAGES = [
    "Home",
    "Search",
    "Tracker",
    "Discography",
    "Eras",
    "Snippets",
    "Grails",
    "Radio",
    "Charts",
    "Group Buys",
    "Producers & Engineers",
    "Community",
    "API"
]

with st.sidebar:

    st.markdown("## 🕊️ WRLD VAULT")

    st.caption("THE ULTIMATE JUICE WRLD ARCHIVE")

    page = st.radio(
        "NAVIGATION",
        PAGES
    )

    st.divider()

    st.caption("JUICE WRLD VAULT · V2")

    st.caption("Powered by juicewrld.io")


st.markdown(
    '<div class="brand">🕊️ JUICE WRLD VAULT '
    '<span class="muted">V2</span></div>'
    '<div class="muted">The archive. The music. The legacy.</div>',
    unsafe_allow_html=True
)


# ============================================================
# HOME
# ============================================================

if page == "Home":

    stats = get_data("/stats")

    st.markdown("""
    <div class="hero">
        <span class="muted">WELCOME TO THE WRLD ARCHIVE</span>
        <h1>Keep the WRLD alive.</h1>
        <p class="muted">
            Explore songs, releases, eras, credits and the music archive.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if isinstance(stats, dict):

        cols = st.columns(5)

        metrics = [
            ("Songs", "songs"),
            ("Versions", "versions"),
            ("Sessions", "studioSessions"),
            ("Eras", "eras"),
            ("People", "people")
        ]

        for column, (label, key) in zip(cols, metrics):

            column.metric(
                label,
                f"{stats.get(key, 0):,}"
            )

        st.divider()

        cols = st.columns(4)

        cols[0].metric("Releases", stats.get("projects", 0))
        cols[1].metric("Playable entries", stats.get("playable", 0))
        cols[2].metric("With lyrics", stats.get("withLyrics", 0))
        cols[3].metric(
            "Studio sessions",
            stats.get("studioSessions", 0)
        )

        by_status = stats.get("byStatus") or {}

        st.subheader("Catalogue breakdown")

        status_cols = st.columns(5)

        for column, status in zip(
            status_cols,
            ["released", "leaked", "unsurfaced", "session", "misc"]
        ):

            column.metric(
                status.title(),
                by_status.get(status, 0)
            )

    else:

        st.warning("Statistics are temporarily unavailable.")

    st.divider()

    st.subheader("Recently explored")

    songs = get_data("/songs", {"limit": 5})

    if isinstance(songs, list):

        for song in songs:
            show_song(song)


# ============================================================
# GLOBAL SEARCH
# ============================================================

elif page == "Search":

    st.subheader("🔎 Search the Vault")

    query = st.text_input(
        "Search everything",
        placeholder="Songs, albums, eras, producers..."
    )

    if query:

        if len(query.strip()) < 2:

            st.info("Enter at least two characters.")

        else:

            results = get_data(
                "/search",
                {"q": query, "limit": 30}
            )

            if isinstance(results, dict):

                st.subheader("Songs")

                for song in results.get("songs", []):
                    show_song(song)

                st.subheader("Eras")

                for era in results.get("eras", []):

                    st.markdown(
                        f"**{era.get('name', 'Unknown')}**"
                    )

                    open_link(era.get("url"))

                st.subheader("Releases")

                for project in results.get("projects", []):

                    st.markdown(
                        f"**{project.get('name', 'Unknown')}**"
                    )

                    open_link(project.get("url"))

                st.subheader("People")

                for person in results.get("people", []):

                    st.markdown(
                        f"**{person.get('name', 'Unknown')}**"
                    )

                    open_link(person.get("url"))


# ============================================================
# TRACKER
# ============================================================

elif page == "Tracker":

    st.subheader("🎵 Song Tracker")

    a, b, c = st.columns([2, 1, 1])

    query = a.text_input("Search songs")

    status = b.selectbox(
        "Status",
        [
            "All",
            "released",
            "leaked",
            "unsurfaced",
            "session",
            "misc"
        ]
    )

    limit = c.selectbox(
        "Results per page",
        [25, 50, 100, 200],
        index=1
    )

    offset = st.number_input(
        "Page offset",
        min_value=0,
        value=0,
        step=limit
    )

    params = {
        "limit": limit,
        "offset": offset
    }

    if query:
        params["q"] = query

    if status != "All":
        params["status"] = status

    songs = get_data("/songs", params)

    if isinstance(songs, list):

        st.caption(f"Showing {len(songs)} entries.")

        for song in songs:

            show_song(song)

            with st.expander(
                f"More information: {song.get('title', 'Song')}"
            ):

                show_song_details(song["id"])

    else:

        st.info("No songs found.")


# ============================================================
# DISCOGRAPHY
# ============================================================

elif page == "Discography":

    st.subheader("💿 Discography")

    projects = get_data("/projects")

    if isinstance(projects, list):

        kind = st.selectbox(
            "Release type",
            ["All", "album", "ep", "single", "collection", "misc"]
        )

        if kind != "All":
            projects = [
                project for project in projects
                if project.get("kind") == kind
            ]

        for project in projects:

            with st.container(border=True):

                left, right = st.columns([1, 4])

                with left:
                    show_cover(project.get("cover"), 160)

                with right:

                    st.markdown(
                        f"### {project.get('name', 'Release')}"
                    )

                    released = project.get("released") or {}

                    st.caption(
                        f"{project.get('kind', 'Release').title()} "
                        f"· {project.get('era') or 'Unknown era'} "
                        f"· {released.get('text', 'Unknown date')}"
                    )

                    st.caption(
                        f"{project.get('trackCount', 0)} tracks"
                    )

                    if project.get("slug"):

                        with st.expander("View tracklist"):

                            details = get_data(
                                f"/projects/{project['slug']}"
                            )

                            if isinstance(details, dict):

                                for index, track in enumerate(
                                    details.get("tracks", []),
                                    start=1
                                ):

                                    st.write(
                                        f"{index}. "
                                        f"{track.get('title', 'Unknown')}"
                                    )

                                    open_link(track.get("url"))


# ============================================================
# ERAS
# ============================================================

elif page == "Eras":

    st.subheader("🕰️ Juice WRLD Eras")

    eras = get_data("/eras")

    if isinstance(eras, list):

        for era in eras:

            with st.container(border=True):

                left, right = st.columns([1, 4])

                with left:
                    show_cover(era.get("cover"), 170)

                with right:

                    st.markdown(
                        f"### {era.get('name', 'Unknown era')}"
                    )

                    st.caption(
                        f"{era.get('code', '')} "
                        f"· {era.get('start', {}).get('text', '')} "
                        f"— {era.get('end', {}).get('text', '')}"
                    )

                    counts = era.get("counts") or {}

                    st.write(
                        f"Songs: {counts.get('songs', 0)} "
                        f"· Versions: {counts.get('versions', 0)} "
                        f"· Sessions: {counts.get('studioSessions', 0)}"
                    )

                    with st.expander("Explore era"):

                        details = get_data(
                            f"/eras/{era.get('code')}"
                        )

                        if isinstance(details, dict):

                            st.write(
                                details.get(
                                    "description",
                                    "No description available."
                                )
                            )

                            for release in details.get("releases", []):

                                st.write(
                                    f"💿 {release.get('name', 'Release')}"
                                )

                                open_link(release.get("url"))


# ============================================================
# PRODUCERS AND ENGINEERS
# ============================================================

elif page == "Producers & Engineers":

    st.subheader("🎚️ Producers & Engineers")

    query = st.text_input(
        "Find a producer or engineer",
        placeholder="Search a name..."
    )

    params = {"limit": 100}

    if query:
        params["q"] = query

    people = get_data("/people", params)

    if isinstance(people, list):

        st.caption(f"{len(people)} people shown.")

        for person in people:

            with st.container(border=True):

                st.markdown(
                    f"### {person.get('name', 'Unknown')}"
                )

                a, b, c = st.columns(3)

                a.metric("Songs", person.get("songs", 0))
                b.metric("Produced", person.get("produced", 0))
                c.metric("Engineered", person.get("engineered", 0))

                with st.expander("View credits"):

                    details = get_data(
                        f"/people/{person.get('slug')}"
                    )

                    if isinstance(details, dict):

                        for credit in details.get("credits", []):

                            st.write(
                                f"• {credit.get('title', 'Unknown')} "
                                f"({', '.join(credit.get('roles', []))})"
                            )

                            open_link(credit.get("url"))


# ============================================================
# RADIO
# ============================================================

elif page == "Radio":

    st.subheader("📻 WRLD Radio")

    st.markdown("""
    <div class="hero">
        <span class="muted">JUICE WRLD RADIO</span>
        <h1>Let the music play.</h1>
        <p class="muted">
            Discover a random entry from the catalogue.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "radio_song" not in st.session_state:
        st.session_state.radio_song = None

    if st.button("🎲 Shuffle a song"):

        songs = get_data(
            "/songs",
            {"limit": 200}
        )

        if isinstance(songs, list) and songs:

            st.session_state.radio_song = random.choice(songs)

    song = st.session_state.radio_song

    if song:

        show_song(song)

        st.info(
            "The catalogue API does not expose downloadable audio. "
            "Use the song page to listen."
        )

    else:

        st.info("Press shuffle to discover a song.")


# ============================================================
# SNIPPETS
# ============================================================

elif page == "Snippets":

    st.subheader("🎬 Snippets & Footage")

    st.info(
        "This section needs the Juice WRLD media archive connection. "
        "The catalogue API does not provide snippet video files."
    )

    st.markdown(
        "Media source: `https://juicewrldapi.com`"
    )


# ============================================================
# GRAILS
# ============================================================

elif page == "Grails":

    st.subheader("🏆 Grails")

    st.info(
        "Grails need a dedicated dataset or media API route. "
        "No grail endpoint is exposed by the catalogue API."
    )


# ============================================================
# CHARTS
# ============================================================

elif page == "Charts":

    st.subheader("📊 Vault Charts")

    stats = get_data("/stats")

    if isinstance(stats, dict):

        by_status = stats.get("byStatus") or {}

        st.metric(
            "Total versions",
            stats.get("versions", 0)
        )

        st.metric(
            "Released songs",
            by_status.get("released", 0)
        )

        st.metric(
            "Leaked songs",
            by_status.get("leaked", 0)
        )

        st.metric(
            "Unsurfaced songs",
            by_status.get("unsurfaced", 0)
        )

        st.metric(
            "Catalogue plays",
            (stats.get("plays") or {}).get("site", 0)
        )


# ============================================================
# GROUP BUYS
# ============================================================

elif page == "Group Buys":

    st.subheader("💰 Group Buys")

    stats = get_data("/stats")

    if isinstance(stats, dict):

        buys = stats.get("groupBuys") or {}

        a, b, c, d = st.columns(4)

        a.metric("Total", buys.get("total", 0))
        b.metric("Finished", buys.get("finished", 0))
        c.metric("Failed", buys.get("failed", 0))
        d.metric("Unknown", buys.get("unknown", 0))

    st.info(
        "Detailed group-buy listings require a separate group-buy "
        "dataset. These statistics come from the catalogue API."
    )


# ============================================================
# COMMUNITY
# ============================================================

elif page == "Community":

    st.subheader("💬 Vault Community")

    st.info(
        "Community posts, comments and suggestions require a database "
        "and backend. The public catalogue API is read-only."
    )


# ============================================================
# API
# ============================================================

elif page == "API":

    st.subheader("🔌 Developer API")

    st.markdown("""
    Connect your Discord bot or another application to the
    Juice WRLD catalogue.
    """)

    st.markdown("### Base URL")

    st.code("https://juicewrld.io/api/v1")

    st.markdown("### Available endpoints")

    st.code("""
GET /songs
GET /songs/{id}

GET /eras
GET /eras/{code}

GET /projects
GET /projects/{slug}

GET /people
GET /people/{slug}

GET /search?q=lucid

GET /stats
""", language="http")

    st.markdown("### Example Python request")

    st.code("""
import requests

API = "https://juicewrld.io/api/v1"

response = requests.get(
    f"{API}/search",
    params={"q": "Lucid Dreams", "limit": 10}
)

data = response.json()["data"]

for song in data["songs"]:
    print(song["title"], song["url"])
""", language="python")

    st.markdown("### API documentation")

    st.link_button(
        "Open official API documentation ↗",
        "https://juicewrld.io/developers"
    )

    st.caption(
        "Catalogue data provided by juicewrld.io. "
        "This is a public read-only API."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown("""
<div style="text-align:center;color:#64748b;padding:20px;">
    🕊️ JUICE WRLD VAULT V2<br>
    <small>Preserving the WRLD, one track at a time.</small><br>
    <small>Catalogue data: juicewrld.io</small>
</div>
""", unsafe_allow_html=True)