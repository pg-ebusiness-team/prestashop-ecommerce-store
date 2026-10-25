def get_page_count(soup):

    pagination = soup.find('ul', class_='page-list')

    if pagination is None:
        return 1

    pages = [
        int(a.get_text(strip=True))
        for a in pagination
        if a.get_text(strip=True).isdigit()
    ]

    total_pages = max(pages, default=1)

    return total_pages