import json
import os
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


USERNAME = "mussaratshamsher"
OUTPUT = Path("assets/github-activity.svg")


QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    token = os.environ.get("GH_TOKEN")

    if not token:
        raise RuntimeError("GH_TOKEN environment variable is missing.")

    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USERNAME
        }
    }).encode("utf-8")

    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": USERNAME,
        },
        method="POST",
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read().decode("utf-8"))

    if "errors" in result:
        raise RuntimeError(json.dumps(result["errors"], indent=2))

    return result["data"]["user"]["contributionsCollection"]


def generate_svg(calendar):
    weeks = calendar["contributionCalendar"]["weeks"]

    days = []

    for week in weeks:
        for day in week["contributionDays"]:
            days.append(day)

    # GitHub normally returns approximately one year of data.
    days = days[-371:]

    width = 1100
    height = 330

    left = 60
    right = 30
    top = 55
    bottom = 55

    graph_width = width - left - right
    graph_height = height - top - bottom

    if not days:
        raise RuntimeError("No contribution data returned.")

    max_count = max(day["contributionCount"] for day in days)
    if max_count == 0:
        max_count = 1

    points = []

    for index, day in enumerate(days):
        x = left + (
            index / max(1, len(days) - 1)
        ) * graph_width

        y = (
            top
            + graph_height
            - (day["contributionCount"] / max_count) * graph_height
        )

        points.append((x, y))

    line_points = " ".join(
        f"{x:.2f},{y:.2f}"
        for x, y in points
    )

    area_points = (
        f"{left},{top + graph_height} "
        + line_points
        + f" {left + graph_width},{top + graph_height}"
    )

    total = calendar["contributionCalendar"]["totalContributions"]

    latest = days[-1]["date"]
    first = days[0]["date"]

    svg = f"""<svg
xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}"
role="img"
aria-label="GitHub activity graph for {USERNAME}"
>

<rect
    width="100%"
    height="100%"
    rx="12"
    fill="transparent"
/>

<text
    x="{left}"
    y="28"
    font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    font-size="18"
    font-weight="600"
    fill="#24292f"
>
    GitHub Activity
</text>

<text
    x="{width - right}"
    y="28"
    text-anchor="end"
    font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    font-size="13"
    fill="#57606a"
>
    {total:,} contributions
</text>

<line
    x1="{left}"
    y1="{top + graph_height}"
    x2="{left + graph_width}"
    y2="{top + graph_height}"
    stroke="#d0d7de"
    stroke-width="1"
/>

<line
    x1="{left}"
    y1="{top + graph_height * 0.5}"
    x2="{left + graph_width}"
    y2="{top + graph_height * 0.5}"
    stroke="#d8dee4"
    stroke-width="1"
    stroke-dasharray="4 4"
/>

<polygon
    points="{area_points}"
    fill="#2da44e"
    opacity="0.10"
/>

<polyline
    points="{line_points}"
    fill="none"
    stroke="#2da44e"
    stroke-width="3"
    stroke-linejoin="round"
    stroke-linecap="round"
/>

<text
    x="{left}"
    y="{height - 20}"
    font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    font-size="12"
    fill="#57606a"
>
    {first}
</text>

<text
    x="{width - right}"
    y="{height - 20}"
    text-anchor="end"
    font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif"
    font-size="12"
    fill="#57606a"
>
    {latest}
</text>

</svg>
"""

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")

    print(f"Generated {OUTPUT}")
    print(f"Total contributions: {total}")


if __name__ == "__main__":
    calendar = fetch_contributions()
    generate_svg(calendar)
