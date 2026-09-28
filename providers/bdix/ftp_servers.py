from typing import List


def make_bdix_server(name, url, category, description, speed="100Mbps - 1Gbps", status="Active"):
    """Creates a BDIX server dictionary."""
    return {
        "name": str(name),
        "url": str(url),
        "category": str(category),
        "description": str(description),
        "speed": str(speed),
        "status": str(status),
    }


# Popular and reliable BDIX media servers and FTP directories in Bangladesh
POPULAR_BDIX_SERVERS: List[dict] = [
    make_bdix_server(
        name="CircleFTP",
        url="http://ftp.circleftp.net",
        category="Movies & Series",
        description="Largest BDIX FTP server in Bangladesh with high-speed direct media downloads.",
        speed="Up to 1Gbps (BDIX)",
    ),
    make_bdix_server(
        name="DhakaFlix",
        url="http://dhakaflix.org",
        category="Streaming & Movies",
        description="Fast BDIX on-demand streaming and movie download portal.",
        speed="High Speed BDIX",
    ),
    make_bdix_server(
        name="FTPBD / SamOnline",
        url="http://ftpbd.net",
        category="Movies, Games & Software",
        description="SAM Online BDIX FTP server featuring HD/4K movies and PC releases.",
        speed="100Mbps+",
    ),
    make_bdix_server(
        name="RoarFTP",
        url="http://roarftp.com",
        category="Movies & Series",
        description="Comprehensive media directory accessible via major Bangladesh ISP peering.",
        speed="BDIX Peered",
    ),
    make_bdix_server(
        name="ShowTime BD",
        url="http://showtime.com.bd",
        category="Bollywood & Hollywood",
        description="Popular entertainment FTP server with multi-resolution video links.",
        speed="High Speed BDIX",
    ),
    make_bdix_server(
        name="NaturalBD",
        url="http://naturalbd.com",
        category="Full-HD Media Hub",
        description="High availability BDIX server with direct MKV/MP4 links.",
        speed="1Gbps Peered",
    ),
    make_bdix_server(
        name="Discovery FTP",
        url="http://discoveryftp.net",
        category="Documentaries & Movies",
        description="Dedicated BDIX mirror for educational, documentary, and movie content.",
        speed="BDIX Peered",
    ),
    make_bdix_server(
        name="AmberIT Media Server",
        url="http://ftp.amberit.com.bd",
        category="ISP Direct FTP",
        description="Amber IT optical fiber peered BDIX content server.",
        speed="Gigabit BDIX",
    ),
]
