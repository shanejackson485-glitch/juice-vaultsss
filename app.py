import os
import html
import random
import requests
import streamlit as st
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Juice WRLD Vault",
    page_icon="🕊️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CATALOG_API = os.getenv(
    "CATALOG_API_URL",
    "https://juicewrld.io/api/v1"
).rstrip("/")

# This is the JuiceWRLDAPI media root, not localhost.
MEDIA_API = os.getenv(
    "MEDIA_API_URL",
    "https://juicewrldapi.com/juicewrld"
).rstrip("/")

API_KEY = os.getenv("VAULT_API_KEY")
HEADERS = {}
if API_KEY:
    HEADERS["X-API-Key"] = API_KEY

REQUEST_TIMEOUT = 25
DOWNLOAD_TIMEOUT = 45

# Reuse connections rather than creating a new TCP connection for every request.
HTTP = requests.Session()
HTTP.headers.update(HEADERS)


# ============================================================
# STYLING
# ============================================================

st.markdown("""
<style>
@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
);
html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}
.stApp {
    background:
        radial-gradient(
            circle at 80% 0%,
            rgba(37,99,235,.13),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #080a10,
            #111722 55%,
            #090b11
        );
    color: #e8edf7;
}
#MainMenu, footer, header {
    visibility: hidden;
}
.block-container {
    padding-top: 1.3rem;
    padding-bottom: 130px;
    max-width: 1550px;
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
            rgba(37,99,235,.24),
            rgba(15,23,42,.55)
        );
    margin: 20px 0 25px;
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
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
}
div[data-testid="stMetric"] {
    background: #121925;
    border: 1px solid #263244;
    padding: 15px;
    border-radius: 14px;
}
.stButton > button {
    border-radius: 10px;
    border: 1px solid #334155;
    background: #17263d;
    color: white;
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
# REQUEST HELPERS
# ============================================================

def request_json(url, params=None):
    """Request JSON from either upstream API and show useful errors."""
    try:
        response = HTTP.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as error:
        status = (
            error.response.status_code
            if error.response is not None
            else "Unknown"
        )
        st.error(f"API returned HTTP {status}.")
        with st.expander("Request details"):
            st.code(str(error))

    except requests.exceptions.ConnectionError as error:
        st.error(
            "Could not connect to the API. Check that the upstream API "
            "is online and that the configured URL is correct."
        )
        with st.expander("Connection details"):
            st.code(str(error))

    except requests.exceptions.Timeout:
        st.error("The API request timed out. Please try again.")

    except ValueError:
        st.error("The API returned invalid JSON.")

    except Exception as error:
        st.error(f"Request error: {error}")

    return None


@st.cache_data(ttl=180, show_spinner=False)
def catalog_get(path, params=None):
    return request_json(
        f"{CATALOG_API}/{path.lstrip('/')}",
        params
    )


def media_get(path, params=None):
    return request_json(
        f"{MEDIA_API}/{path.lstrip('/')}",
        params
    )


def unwrap(value):
    if isinstance(value, dict):
        return value.get("data", value)
    return value


def as_list(value):
    value = unwrap(value)

    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        for key in [
            "results",
            "items",
            "files",
            "songs",
            "data"
        ]:
            if isinstance(value.get(key), list):
                return value[key]

    return []


def safe(value, fallback="Unknown"):
    if value is None or value == "":
        return fallback
    return str(value)


def cover(item):
    if not isinstance(item, dict):
        return None

    return (
        item.get("cover")
        or item.get("cover_url")
        or item.get("image")
        or item.get("image_url")
    )


def show_cover(url, width=140):
    if url:
        try:
            st.image(url, width=width)
        except Exception:
            st.caption("Artwork unavailable.")


# ============================================================
# MEDIA URLS
# ============================================================

def media_download_url(path, compressed=True):
    """
    Build a correctly encoded JuiceWRLDAPI download URL.

    The previous version had a mismatched closing parenthesis in the
    urlencode expression, which caused the SyntaxError on line 213.
    """
    endpoint = (
        "files/download-compressed/"
        if compressed
        else "files/download/"
    )

    query = urlencode({
        "path": path,
        "channel": "comp"
    })

    return f"{MEDIA_API}/{endpoint}?{query}"


def media_browse(path=""):
    return media_get(
        "files/browse/",
        {
            "path": path,
            "channel": "comp"
        }
    )


def get_file_path(item):
    if not isinstance(item, dict):
        return ""

    return (
        item.get("path")
        or item.get("full_path")
        or item.get("download_path")
        or ""
    )


def get_file_name(item):
    if not isinstance(item, dict):
        return "Unknown file"

    return (
        item.get("name")
        or item.get("filename")
        or item.get("title")
        or "Unknown file"
    )


def is_directory(item):
    if not isinstance(item, dict):
        return False

    return (
        item.get("is_directory") is True
        or item.get("is_dir") is True
        or item.get("type") in [
            "folder",
            "directory"
        ]
    )


def download_file_bytes(path):
    """Download a file safely; return None if the media server errors."""
    if not path:
        st.warning("This file does not have a download path.")
        return None

    try:
        response = HTTP.get(
            media_download_url(path, compressed=False),
            timeout=DOWNLOAD_TIMEOUT
        )
        response.raise_for_status()

        if not response.content:
            st.warning("The media API returned an empty file.")
            return None

        return response.content

    except requests.RequestException as error:
        st.error("The file could not be downloaded from the media API.")
        with st.expander("Download details"):
            st.code(str(error))
        return None


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "current_track": None,
    "queue": [],
    "recently_played": [],
    "shuffle": False,
    "repeat": False,
    "browse_path": "",
    "selected_song": None,
    "radio_track": None
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# PLAYER
# ============================================================

def play_track(track):
    path = get_file_path(track)

    if not path:
        st.warning("This file has no playable path.")
        return

    st.session_state.current_track = track

    recent = st.session_state.recently_played
    recent.insert(0, track)
    st.session_state.recently_played = recent[:20]


def player():
    track = st.session_state.current_track

    if not track:
        return

    name = get_file_name(track)
    path = get_file_path(track)

    st.divider()
    st.markdown("### 🎧 NOW PLAYING")

    left, middle, right = st.columns([1, 4, 1])

    with left:
        show_cover(cover(track), 75)

    with middle:
        st.markdown(f"**{html.escape(name)}**")
        st.caption("JUICE WRLD VAULT PLAYER")

    with right:
        if st.button("✕", key="close_player"):
            st.session_state.current_track = None
            st.rerun()

    if path:
        st.audio(
            media_download_url(path),
            format="audio/mpeg"
        )

        if st.button("Prepare download", key="prepare_current_download"):
            file_data = download_file_bytes(path)
            if file_data:
                st.download_button(
                    "⬇ Download file",
                    data=file_data,
                    file_name=os.path.basename(path) or "juice-wrld-audio",
                    mime="application/octet-stream",
                    key="download_current"
                )

    controls = st.columns(3)

    with controls[0]:
        if st.button("🔀 Shuffle", key="player_shuffle"):
            st.session_state.shuffle = (
                not st.session_state.shuffle
            )
            st.caption(
                "Shuffle is " +
                ("on" if st.session_state.shuffle else "off")
            )

    with controls[1]:
        if st.button("🔁 Repeat", key="player_repeat"):
            st.session_state.repeat = (
                not st.session_state.repeat
            )
            st.caption(
                "Repeat is " +
                ("on" if st.session_state.repeat else "off")
            )

    with controls[2]:
        st.caption(
            f"Queue: {len(st.session_state.queue)}"
        )


# ============================================================
# SONG CARDS
# ============================================================

def song_card(song):
    title = safe(
        song.get("title")
        or song.get("name")
    )

    with st.container(border=True):
        left, right = st.columns([1, 4])

        with left:
            show_cover(cover(song), 115)

        with right:
            st.markdown(f"### {html.escape(title)}")
            st.caption(
                f"{safe(song.get('status')).upper()} "
                f"· {safe(song.get('era'))}"
            )

            duration = song.get("duration") or {}

            if isinstance(duration, dict):
                duration = duration.get("text", "")

            st.caption(
                f"Duration: {safe(duration)}"
            )

            song_url = song.get("url")
            if song_url:
                st.link_button(
                    "Open song ↗",
                    song_url
                )

            song_id = song.get("id")
            if song_id is not None:
                if st.button(
                    "Song details",
                    key=f"detail_{song_id}"
                ):
                    st.session_state.selected_song = song_id
                    st.rerun()


# ============================================================
# MEDIA FILE CARD
# ============================================================

def media_file_card(item):
    name = get_file_name(item)
    path = get_file_path(item)
    folder = is_directory(item)

    with st.container(border=True):
        if folder:
            st.markdown(f"📁 **{html.escape(name)}**")

            if st.button(
                f"Open folder: {name}",
                key=f"open_{path}_{name}"
            ):
                st.session_state.browse_path = path or name
                st.rerun()

        else:
            extension = os.path.splitext(name)[1].lower()
            st.markdown(f"🎵 **{html.escape(name)}**")

            if extension in [
                ".mp3",
                ".m4a",
                ".wav",
                ".ogg",
                ".flac",
                ".aac"
            ]:
                if st.button(
                    "▶ Play",
                    key=f"play_{path}_{name}"
                ):
                    play_track(item)
                    st.rerun()

            elif extension in [
                ".mp4",
                ".mov",
                ".webm",
                ".m4v"
            ]:
                if path:
                    st.video(
                        media_download_url(
                            path,
                            compressed=False
                        )
                    )

            else:
                st.caption("Archive file")

            if path:
                st.link_button(
                    "Download ↗",
                    media_download_url(
                        path,
                        compressed=False
                    )
                )


# ============================================================
# SIDEBAR
# ============================================================

PAGES = [
    "Home",
    "Search",
    "Tracker",
    "Discography",
    "Eras",
    "Snippets",
    "Grails",
    "Sessions",
    "Radio",
    "Charts",
    "Producers & Engineers",
    "Recently Played",
    "Community",
    "API"
]

with st.sidebar:
    st.markdown("## 🕊️ WRLD VAULT")
    st.caption("THE JUICE WRLD ARCHIVE")

    page = st.radio(
        "NAVIGATION",
        PAGES
    )

    st.divider()
    st.caption("V2 · THE ARCHIVE")
    st.caption("999 FOREVER")


# ============================================================
# HEADER
# ============================================================

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
    st.markdown("""
    <div class="hero">
        <span class="muted">WELCOME TO THE WRLD ARCHIVE</span>
        <h1>Keep the WRLD alive.</h1>
        <p class="muted">
            Discover music, albums, eras, sessions and unreleased history.
        </p>
    </div>
    """, unsafe_allow_html=True)

    stats = unwrap(catalog_get("stats"))

    if isinstance(stats, dict):
        cols = st.columns(5)

        for column, label, key in zip(
            cols,
            ["Songs", "Versions", "Sessions", "Eras", "People"],
            ["songs", "versions", "studioSessions", "eras", "people"]
        ):
            column.metric(
                label,
                stats.get(key, 0)
            )

    st.divider()
    st.subheader("🔎 Search the Vault")

    query = st.text_input(
        "Search",
        placeholder="Search Juice WRLD songs..."
    )

    if query:
        results = unwrap(
            catalog_get(
                "search",
                {"q": query, "limit": 15}
            )
        )

        if isinstance(results, dict):
            for song in results.get("songs", []):
                song_card(song)

    st.divider()
    st.subheader("🎵 Explore the archive")

    songs = as_list(
        catalog_get("songs", {"limit": 8})
    )

    for song in songs:
        song_card(song)


# ============================================================
# SEARCH
# ============================================================

elif page == "Search":
    st.subheader("🔎 Global Search")

    query = st.text_input(
        "Search songs, albums, eras and people"
    )

    if query:
        results = unwrap(
            catalog_get(
                "search",
                {"q": query, "limit": 40}
            )
        )

        if isinstance(results, dict):
            for section in [
                "songs",
                "projects",
                "eras",
                "people"
            ]:
                st.subheader(section.title())

                for item in results.get(section, []):
                    st.markdown(
                        f"**{html.escape(safe(item.get('title') or item.get('name')))}**"
                    )

                    if item.get("url"):
                        st.link_button(
                            "Open ↗",
                            item["url"]
                        )


# ============================================================
# TRACKER
# ============================================================

elif page == "Tracker":
    st.subheader("🎵 Song Tracker")

    a, b, c = st.columns([2, 1, 1])

    query = a.text_input("Song search")

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
        "Results",
        [25, 50, 100, 200]
    )

    offset = st.number_input(
        "Offset",
        min_value=0,
        step=25
    )

    params = {
        "limit": limit,
        "offset": offset
    }

    if query:
        params["q"] = query

    if status != "All":
        params["status"] = status

    songs = as_list(
        catalog_get("songs", params)
    )

    st.caption(f"{len(songs)} results loaded")

    for song in songs:
        song_card(song)


# ============================================================
# SONG DETAILS
# ============================================================

if (
    st.session_state.selected_song
    and page == "Tracker"
):
    st.divider()

    song_id = st.session_state.selected_song

    details = unwrap(
        catalog_get(f"songs/{song_id}")
    )

    if isinstance(details, dict):
        st.subheader("Song details")
        st.title(
            safe(details.get("title"))
        )
        show_cover(
            cover(details),
            220
        )
        st.json(details)


# ============================================================
# DISCOGRAPHY
# ============================================================

elif page == "Discography":
    st.subheader("💿 Discography")

    projects = as_list(
        catalog_get("projects")
    )

    for project in projects:
        with st.container(border=True):
            left, right = st.columns([1, 4])

            with left:
                show_cover(
                    cover(project),
                    160
                )

            with right:
                st.markdown(
                    f"### {html.escape(safe(project.get('name')))}"
                )

                st.caption(
                    f"{safe(project.get('kind'))} "
                    f"· {safe(project.get('era'))}"
                )

                if project.get("slug"):
                    if st.button(
                        "View tracklist",
                        key=f"project_{project['slug']}"
                    ):
                        st.session_state[
                            "selected_project"
                        ] = project["slug"]

                if project.get("url"):
                    st.link_button(
                        "Open release ↗",
                        project["url"]
                    )

    selected = st.session_state.get(
        "selected_project"
    )

    if selected:
        st.divider()
        st.subheader("Tracklist")

        details = unwrap(
            catalog_get(f"projects/{selected}")
        )

        if isinstance(details, dict):
            for index, track in enumerate(
                details.get("tracks", []),
                1
            ):
                st.write(
                    f"{index}. {safe(track.get('title'))}"
                )


# ============================================================
# ERAS
# ============================================================

elif page == "Eras":
    st.subheader("🕰️ Juice WRLD Eras")

    eras = as_list(
        catalog_get("eras")
    )

    for era in eras:
        with st.container(border=True):
            show_cover(
                cover(era),
                150
            )

            st.markdown(
                f"### {html.escape(safe(era.get('name')))}"
            )

            st.caption(
                f"Era code: {safe(era.get('code'))}"
            )

            code = era.get("code")

            if code:
                if st.button(
                    "Explore era",
                    key=f"era_{code}"
                ):
                    st.session_state["selected_era"] = code

    selected = st.session_state.get("selected_era")

    if selected:
        st.divider()

        details = unwrap(
            catalog_get(f"eras/{selected}")
        )

        if isinstance(details, dict):
            st.json(details)


# ============================================================
# MEDIA BROWSER
# ============================================================

elif page in [
    "Snippets",
    "Grails",
    "Sessions"
]:
    section = {
        "Snippets": "Snippets",
        "Grails": "Grails",
        "Sessions": "Session Edits"
    }[page]

    st.subheader(
        {
            "Snippets": "🎬 Snippets & Footage",
            "Grails": "🏆 Grails Archive",
            "Sessions": "🎙️ Studio Sessions"
        }[page]
    )

    st.caption(
        "Browse the Juice WRLD media archive."
    )

    if st.button("⬅ Back to root"):
        st.session_state.browse_path = ""
        st.rerun()

    path = st.session_state.browse_path or section

    st.markdown(
        f"**Current folder:** `{path}`"
    )

    result = media_browse(path)

    if result is not None:
        files = as_list(result)

        if not files:
            st.info(
                "No files were returned. The folder may be empty "
                "or the API may use a different response format."
            )

        else:
            search = st.text_input(
                "Filter files",
                key=f"filter_{page}"
            )

            if search:
                files = [
                    item for item in files
                    if search.lower() in get_file_name(item).lower()
                ]

            st.caption(
                f"{len(files)} files and folders"
            )

            for item in files:
                media_file_card(item)


# ============================================================
# RADIO
# ============================================================

elif page == "Radio":
    st.subheader("📻 999 FM")

    st.markdown("""
    <div class="hero">
        <span class="muted">JUICE WRLD RADIO</span>
        <h1>Let the WRLD play.</h1>
        <p class="muted">
            Random discoveries from the archive.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎲 Shuffle random track"):
        result = unwrap(
            media_get("radio/random/")
        )

        if isinstance(result, dict):
            track = result

            # Some API responses wrap the selected file in a nested object.
            if isinstance(track.get("data"), dict):
                track = track["data"]

            st.session_state.radio_track = track

            if get_file_path(track):
                play_track(track)

            st.rerun()

        else:
            st.error(
                "Radio returned an unexpected response."
            )

    track = st.session_state.radio_track

    if track:
        st.subheader(
            safe(
                track.get("name")
                or track.get("title")
            )
        )

        path = get_file_path(track)

        if path:
            st.audio(
                media_download_url(path),
                format="audio/mpeg"
            )
        else:
            st.json(track)

    else:
        st.info(
            "Press shuffle to discover a random track."
        )


# ============================================================
# CHARTS
# ============================================================

elif page == "Charts":
    st.subheader("📊 Vault Statistics")

    stats = unwrap(
        catalog_get("stats")
    )

    if isinstance(stats, dict):
        st.json(stats)
    else:
        st.info("Statistics unavailable.")


# ============================================================
# PRODUCERS / ENGINEERS
# ============================================================

elif page == "Producers & Engineers":
    st.subheader("🎚️ Producers & Engineers")

    query = st.text_input(
        "Find a person"
    )

    params = {"limit": 100}

    if query:
        params["q"] = query

    people = as_list(
        catalog_get("people", params)
    )

    for person in people:
        with st.container(border=True):
            st.markdown(
                f"### {html.escape(safe(person.get('name')))}"
            )

            st.caption(
                f"Songs: {person.get('songs', 0)}"
            )

            slug = person.get("slug")

            if slug:
                if st.button(
                    "View profile",
                    key=f"person_{slug}"
                ):
                    st.session_state["selected_person"] = slug

    selected = st.session_state.get("selected_person")

    if selected:
        details = unwrap(
            catalog_get(f"people/{selected}")
        )

        if isinstance(details, dict):
            st.json(details)


# ============================================================
# RECENTLY PLAYED
# ============================================================

elif page == "Recently Played":
    st.subheader("🕘 Recently Played")

    for index, track in enumerate(
        st.session_state.recently_played
    ):
        name = get_file_name(track)

        st.write(f"🎵 {name}")

        if st.button(
            f"Play {name}",
            key=f"recent_{index}_{name}"
        ):
            play_track(track)
            st.rerun()


# ============================================================
# COMMUNITY
# ============================================================

elif page == "Community":
    st.subheader("💬 Vault Community")

    st.info(
        "Community posts, accounts, comments and suggestions "
        "require a dedicated database and backend."
    )


# ============================================================
# API
# ============================================================

elif page == "API":
    st.subheader("🔌 Developer API")

    st.markdown("### Catalogue API")
    st.code(CATALOG_API)

    st.markdown("### Media API")
    st.code(MEDIA_API)

    st.markdown("### Catalogue endpoints")
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

    st.markdown("### Media endpoints")
    st.code("""
GET /files/browse/?path=Snippets&channel=comp
GET /files/download/?path=FILE_PATH&channel=comp
GET /files/download-compressed/?path=FILE_PATH&channel=comp
GET /radio/random/
""", language="http")

    st.link_button(
        "Open Juice WRLD API ↗",
        "https://juicewrldapi.com/"
    )

    st.link_button(
        "Open Catalogue Documentation ↗",
        "https://juicewrld.io/developers"
    )

    st.caption(
        "The Streamlit website and a Discord bot are separate clients. "
        "A bot should use a public API URL, never 127.0.0.1 on Streamlit Cloud."
    )


# ============================================================
# PLAYER AREA
# ============================================================

player()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown("""
<div style="
    text-align:center;
    color:#64748b;
    padding:20px;
">
    🕊️ JUICE WRLD VAULT<br>
    <small>Preserving the WRLD, one track at a time.</small><br>
    <small>V2 · 999 FOREVER</small>
</div>
""", unsafe_allow_html=True)
