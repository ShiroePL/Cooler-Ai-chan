import py1337x
import json

def format_torrents_as_json(search_results):
    """Convert torrent search results to a presentable JSON format"""
    formatted_results = []
    
    for result in search_results.items:
        formatted_results.append({
            "title": result.name,
            "seeders": result.seeders,
            "leechers": result.leechers,
            "size": result.size,
            "uploader": result.uploader
        })
    
    return json.dumps({
        "results": formatted_results,
        "total_count": len(formatted_results),
        "page": search_results.current_page,
        "total_pages": search_results.page_count
    }, indent=2)

torrents = py1337x.Py1337x()

# Basic search
results = torrents.search('The Precinct', page=1)

# Print as JSON
json_output = format_torrents_as_json(results)
print(json_output)

# Search with specific parameters (uncomment if needed)
# results = torrents.search('The Precinct', sort_by=py1337x.sort.SEEDERS, category=py1337x.category.APPS)
# json_output = format_torrents_as_json(results)
# print(json_output)

