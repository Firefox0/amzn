import grequests
from bs4 import BeautifulSoup
import json
import time 

# restructure 
# test time print end="", does it print that one already or waits until full line with newline
# json dump

def get_user_input():
    product_formatted = 0 
    price_range = 0
    pages_amount = 0

    user_input_raw = input("Optional Args: --p 100-300 (Price Range: $100-$300)\n" +
                            "--s 5 (How many amazon pages to check, default: 12)\n" +
                            "What are you looking for?\n")

    if "--" in user_input_raw:
        split = user_input_raw.split("--")
        product_formatted = split[0]
        if " " in product_formatted:
            product_formatted.replace(" ", "+")

        for e in split[1:]:
            arg = e[:2]
            if arg == "p ":
                price_range = e[2:]
                price_range = tuple(map(float, price_range.split("-")))
            elif arg == "s ":
                pages_amount = e[2:] 

    return product_formatted, price_range, int(pages_amount)

def amazon_links(product_formatted, pages_amount=12):
    urls = []
    amazon_standard = "https://www.amazon.com/s?k="
    for i in range(1, pages_amount+1):
        urls.append(f"{amazon_standard}{product_formatted}&page={i}")
    return urls

def make_requests(urls, header):
    print("Starting requests")
    async_requests = (grequests.get(u, headers=header) for u in urls)
    responses = grequests.map(async_requests) 
    print("Requests done")
    return responses

def filter_pages(responses, price_range=None):
    if price_range:
        minimum_range = price_range[0]
        maximum_range = price_range[1]

    filtered = []
    amount_sales_total = 0
    current_page_number = 1

    for response in responses:
        print(f"Checking page: {current_page_number} -> ", end="")
        soup = BeautifulSoup(response.content, "html.parser")
        top_classes = soup.find_all("a", {"class": "a-size-base a-link-normal s-no-hover a-text-normal"})
        sale_classes = [c for c in top_classes if c.find("span", {"class": "a-price a-text-price"})]
        amount_sales_page = 0

        for sale_class in sale_classes: 
            href = sale_class["href"].split("/ref")[0]
            if href == "/gp/slredirect/picassoRedirect.html":
                continue
            prices = sale_class.find_all("span", {"class": "a-offscreen"})
            from_price = float(prices[1].text[1:].replace(",", ""))
            to_price = float(prices[0].text[1:].replace(",", ""))
            if price_range: 
                if not (to_price <= maximum_range and to_price >= minimum_range):
                    continue  
            filtered.append((from_price, to_price, href))
            amount_sales_page += 1

        amount_sales_total += amount_sales_page
        current_page_number += 1
        print(f"Found {amount_sales_page} sales.")
        
    print(f"Checked {amount_sales_total} sales in total.")
    return filtered

def sort_list(l):
    l.sort(key=lambda x: x[0]-x[1], reverse=True)
    return l

def dump_json(l):
    
    d = {h.split("/", 2)[1].replace("-", " "): {"from": f, "to": t, "saving": round(f-t, 2), "link": f"https://www.amazon.com{h}"} for f, t, h in l}
    new_d = sorted(d.items(), key=lambda e: e[1]["saving"], reverse=True)
    print(json.dumps(new_d, indent=4))

def main():
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:68.0) Gecko/20100101 Firefox/68.0"}
    product_formatted, price_range, pages_amount = get_user_input()
    urls = amazon_links(product_formatted, pages_amount=pages_amount)
    responses = make_requests(urls, header)
    filtered_pages = filter_pages(responses, price_range=price_range)
    best_deal = get_best_deal(filtered_pages)
    if best_deal:
        print(f"You save ${round(best_deal[0], 2)} with the best deal: https://www.amazon.com{best_deal[1]}")
    else:
        print("No deals found. Look for another product or change price range.")
    if input("Again? (y/n) ") == "y":
        main()

if __name__ == "__main__":
    main()
