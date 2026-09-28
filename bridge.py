import json
import sys
from providers import get_provider, list_providers



def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No action specified"}))
        return

    action = sys.argv[1]

    try:
        if action == "providers":
            print(json.dumps(list_providers()))

        elif action == "search":
            query = sys.argv[2]
            provider_name = sys.argv[3] if len(sys.argv) > 3 else "moviebox"
            page = int(sys.argv[4]) if len(sys.argv) > 4 else 1
            provider = get_provider(provider_name)
            items = provider["search"](query, page=page)
            print(json.dumps(items))

        elif action == "details":
            media_id = sys.argv[2]
            provider_name = sys.argv[3] if len(sys.argv) > 3 else "moviebox"
            provider = get_provider(provider_name)
            details = provider["get_details"](media_id)
            print(json.dumps(details))

        elif action == "streams":
            media_id = sys.argv[2]
            season = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            episode = int(sys.argv[4]) if len(sys.argv) > 4 else 0
            provider_name = sys.argv[5] if len(sys.argv) > 5 else "moviebox"
            provider = get_provider(provider_name)
            releases = provider["get_streams"](media_id, season=season, episode=episode)
            print(json.dumps(releases))

        elif action == "m3u":
            media_id = sys.argv[2]
            season = int(sys.argv[3]) if len(sys.argv) > 3 else 0
            episode = int(sys.argv[4]) if len(sys.argv) > 4 else 0
            provider_name = sys.argv[5] if len(sys.argv) > 5 else "moviebox"
            host = sys.argv[6] if len(sys.argv) > 6 else None
            provider = get_provider(provider_name)
            releases = provider["get_streams"](media_id, season=season, episode=episode)
            if releases:
                title = releases[0].get("filename") if isinstance(releases[0], dict) else getattr(releases[0], "filename", "Movie")
                m3u_text = generate_m3u_playlist(releases[0], title=title, host=host)
                print(m3u_text)
            else:
                print("#EXTM3U\n")

        else:
            print(json.dumps({"error": f"Unknown action {action}"}))

    except Exception as e:
        print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    main()
